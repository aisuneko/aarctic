import functools
import json
from itertools import islice
import cherrypy
from slob import open as slopen, find, UTF8
import aarctic.utils as utils


URL = functools.partial(cherrypy.url, relative='server')


def shutdown():
    cherrypy.engine.exit()

@cherrypy.expose
class Root:
    def __init__(self, names, limit):
        self.slobs = {}
        for name in names:  # read slob files into an array
            slob = slopen(name)
            self.slobs[slob.id] = slob
        self.lookup = Lookup(self.slobs, limit)
        self.slob = Content(self.slobs)

    def GET(self):
        raise cherrypy.HTTPRedirect(URL('/lookup'))


@cherrypy.expose
class Lookup:

    def __init__(self, slobs, limit):
        self.slobs = slobs
        self.limit = limit

    def GET(self, *args, word=None, limit=None):  # build word list
        if limit is None:
            limit = self.limit
        if word or args:
            limit = int(limit)  # max. number of candidates
            if word is None:
                # wsgi weirdness
                word = args[0].encode('ISO-8859-1').decode(UTF8)
            result = []
            lookup_result = find(word, self.slobs.values())
            for slob, item in islice(lookup_result, limit):  # generate result list
                result.append((slob.id, item))
            entrylist = []
            if result:  # actually found something
                for slob_id, item in result:
                    href = mk_content_link(slob_id, item)
                    entrylist.append({
                        'key': item.key,
                        'source': self.slobs[slob_id].tags.get('label', slob_id),
                        'link': href})  # generate word link list
        else:
            entrylist = []
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(entrylist, indent=2).encode('utf8')


@cherrypy.expose
class Content:
    # TODO: understand the purpose of those cache headers below
    def __init__(self, slobs):
        self.slobs = slobs

    def to_info(self, s):
        # too bloated here. might clean up unwanted info in the future
        return {
            'id': s.id,
            'compression': s.compression,
            'encoding': s.encoding,
            'blobCount': s.blob_count,
            'refCount': len(s),
            'contentTypes': s.content_types,
            'tags': dict(s.tags)
        }

    def find_slob(self, id_or_uri):  # search for a slob
        slob = self.slobs.get(id_or_uri)
        if slob:
            return slob, True
        for slob in self.slobs.values():
            uri = slob.tags.get('uri')
            if uri and id_or_uri == uri:
                return slob, False

    def GET(self, *args, key=None, blob=None, **_kwargs):
        # args: subdirectory indicator. eg.:
        # /slob: info of all slobs, 0 args
        # /slob/{slob_id}: info of single slob with id slob_id, 1 arg
        # /slob/{slob_id}/{key} HTML definition page of {key} in dict {slob_id}, >= 2 args
        if len(args) == 0:  # info of all slobs
            cherrypy.response.headers['Content-Type'] = 'application/json'
            # get slob info as json
            data = [self.to_info(s) for s in self.slobs.values()]
            return json.dumps(data, indent=2).encode('utf8')
        if len(args) == 1:  # info of one specific slob
            slob_id_or_uri = args[0]
            slob, _ = self.find_slob(slob_id_or_uri)
            if slob:
                cherrypy.response.headers['Content-Type'] = 'application/json'
                cherrypy.response.headers['Cache-Control'] = 'no-cache'
                return json.dumps(self.to_info(slob), indent=2).encode('utf8')
            else:
                raise cherrypy.NotFound

        blob_id = blob

        if len(args) >= 2:  # HTML PAGE of query definition
            key = '/'.join(args[1:])  # get query

        slob_id_or_uri = args[0]
        if_none_match = cherrypy.request.headers.get("If-None-Match")
        slob, is_slob_id = self.find_slob(slob_id_or_uri)  # get target dict

        if not slob:
            raise cherrypy.NotFound

        if is_slob_id and blob_id:  # retrieve entry content
            content_type, content = slob.get(int(blob_id))
            cherrypy.response.headers['Content-Type'] = content_type
            cherrypy.response.headers['Cache-Control'] = 'no-cache'
            #cherrypy.response.headers['Cache-Control'] = 'max-age=31556926'
            return content

        if key and if_none_match:  # request validation
            e_tag = 'f"{slob.id}"'
            if if_none_match == e_tag:
                cherrypy.response.status = 304
                return

        # wsgi weirdness
        key = key.encode('ISO-8859-1').decode('utf8')

        for slob, item in find(key, slob, match_prefix=False):
            if is_slob_id:
                cherrypy.response.headers['Cache-Control'] = 'no-cache'
                #cherrypy.response.headers['Cache-Control'] = 'max-age=31556926'
            else:
                cherrypy.response.headers['Cache-Control'] = 'no-cache'
                #cherrypy.response.headers['Cache-Control'] = 'max-age=600'
                e_tag = 'f"{slob.id}"'
                cherrypy.response.headers['ETag'] = e_tag
            cherrypy.response.headers['Content-Type'] = item.content_type

            return item.content

        cherrypy.response.status = 404
        return None


def mk_content_link(slob_id, item):  # generate entry item url
    href = f"/slob/{slob_id}/{item.key}?blob={item.id}#{item.fragment}"
    return URL(href)


def main(location, limit, port):
    #dict_list = glob.glob("../test_dict/*.slob")
    dict_list = utils.get_dicts(location)
    cherrypy.config.update({
        'server.socket_port': port,
        'server.socket_host': utils.INTERFACE,
        'server.thread_pool': 4,
        'server.shutdown_timeout': 1,
        'tools.encode.on': False,
        'tools.gzip.on': True,
        'tools.caching.on': False,
        'tools.caching.delay': 1
    })
    config = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    cherrypy.quickstart(Root(dict_list, limit),
                        '/', config=config)


if __name__ == '__main__':
    main("../test_dict", 100, 7036) # debug
