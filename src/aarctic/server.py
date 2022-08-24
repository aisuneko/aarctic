import json
from itertools import islice
from bottle import route, run, response, request
from slob import open as slopen, find, UTF8
import aarctic.utils as utils


class Lookup:
    def __init__(self, slobs, limit):
        self.slobs = slobs
        self.limit = limit

    def GET(self, word=None, limit=None):  # build word list
        args = request.query
        if limit is None:
            limit = self.limit
        if word or args:
            limit = int(limit)  # max. number of candidates
            if word is None:
                # wsgi weirdness
                word = args['word'].encode('ISO-8859-1').decode(UTF8)
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
        response.headers.content_type = 'application/json'
        return json.dumps(entrylist, indent=2).encode('utf8')


class Content:
    # I need to better understand the purpose of those headers below

    def __init__(self, slobs):
        self.slobs = slobs

    def to_info(self, s):
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

    def all_slobs_info(self):
        response.headers.content_type = 'application/json'
        data = [self.to_info(s) for s in self.slobs.values()]
        return json.dumps(data, indent=2).encode('utf8')

    def single_slob_info(self, slob_id_or_uri):
        slob, _ = self.find_slob(slob_id_or_uri)
        if slob:
            response.headers.content_type = 'application/json'
            response.headers.cache_control = 'no-store'
            return json.dumps(self.to_info(slob), indent=2).encode('utf8')
        else:
            response.status_code = 404

    def GET(self, slob_id_or_uri, key=None, **_kwargs):
        # args: subdirectory indicator. eg.:
        # /slob: info of all slobs, 0 args
        # /slob/{slob_id}: info of single slob with id slob_id, 1 arg
        # /slob/{slob_id}/{key} HTML definition page of {key} in dict {slob_id}, >= 2 args
        try:
            blob_id = request.query['blob']
        except KeyError:
            blob_id = None
        # key = '/'.join(args[1:])  # get query

        if_none_match = request.get_header('if_none_match')
        slob, is_slob_id = self.find_slob(slob_id_or_uri)  # get target dict

        if not slob:
            response.status_code = 404

        if is_slob_id and blob_id:  # retrieve entry content
            content_type, content = slob.get(int(blob_id))
            response.headers.content_type = content_type
            response.headers.cache_control = 'max-age=31556926'
            return content

        if key and if_none_match:  # request validation
            e_tag = 'f"{slob.id}"'
            if if_none_match == e_tag:
                response.status_code = 304
                return

        # wsgi weirdness
        key = key.encode('ISO-8859-1').decode('utf8')
        for slob, item in find(key, slob, match_prefix=False):
            if is_slob_id:
                response.headers.cache_control = 'max-age=31556926'
            else:
                response.headers.cache_control = 'max-age=600'
                e_tag = 'f"{slob.id}"'
                response.headers.etag = e_tag
            response.headers.content_type = item.content_type
            return item.content

        response.status_code = 404
        return None


def mk_content_link(slob_id, item):  # generate entry item url
    href = f"/slob/{slob_id}/{item.key}?blob={item.id}#{item.fragment}"
    return href


def main(location, limit, port):
    dict_list = utils.get_dicts(location)
    dicts = {}
    for name in dict_list:  # read slob files into an array
        slob = slopen(name)
        dicts[slob.id] = slob
    lookup = Lookup(dicts, limit)
    slobs = Content(dicts)
    route('/')(lookup.GET)
    route('/lookup')(lookup.GET)
    route('/slob')(slobs.all_slobs_info)
    route('/slob/<slob_id_or_uri>')(slobs.single_slob_info)
    route('/slob/<slob_id_or_uri>/<key:path>')(slobs.GET)
    run(host=utils.INTERFACE, port=port, quiet=(not utils.debug))


if __name__ == '__main__':
    main("../test_dict", 100, 7036)  # debug
