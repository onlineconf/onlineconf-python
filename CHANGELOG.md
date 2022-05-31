# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1]
### Added
- Add `get_event_loop`


## [1.0.0]
### Added
- Support Python 3.9, 3.10
- Version control
### Changed
- Replace `asyncio.get_event_loop` to `asyncio.get_running_loop` for compatibility with new versions of Python
- github CI


## [0.1.0]
### Added
Implementation of following methods:
- Config
    - read
    - get
    - items
    - keys
    - values
    - fill_from_yaml
    - shutdown

[Unreleased]: https://github.com/onlineconf/onlineconf-python/compare/master...1.0.1
[1.0.1]: https://github.com/onlineconf/onlineconf-python/compare/v1.0.1...v1.0.0
[1.0.0]: https://github.com/onlineconf/onlineconf-python/compare/v1.0.0...v0.1.0
[0.1.0]: https://github.com/onlineconf/onlineconf-python/compare/v0.1.0
