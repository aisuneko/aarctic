# aarctic

Simplistic PyQt5 desktop client for [Aard2](https://aarddict.org). 

![](screenshot.png)

## Installation & Usage
Clone repository and `pip install .`, then start from shell with  `aarctic`.

You may want to get some .slob dictionaries [here](https://github.com/itkach/slob/wiki/Dictionaries).

## Known Issues
- No prebuilt binaries... for now. I've tried several packaging solutions tirelessly - pyinstaller, briefcase, etc - and failed. I really don't know a thing on how to build and package PyQt applications properly. For now you need to `pip install` it yourself though a .desktop file for Linux is provided. I'm sorry...
- High memory usage (~50MB idle) - possibly due to PyQt limitations and the use of a HTTP server backend (CherryPy). Tried to optimize but with little progress; will continue working on it in the future.
- Slight lag when returning results with lots of dictionaries loaded - will (perhaps) switch to a different backend (say Falcon?) in the future for better performance.

> In short, I really lack real-world experience in this field... Looking forward to having someone tutor me :(
## Changelog
see [CHANGELOG.md](CHANGELOG.md).

## TODO
- [ ] Better support for keyboard control
- [ ] Full Dark Mode / dictionary custom CSS theme support
- [ ] **Optimize performance**

## License 
MIT
