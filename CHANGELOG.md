# Changelog

## [0.10.1](https://github.com/Pushikoo/Pushikoo/compare/v0.10.0...v0.10.1) (2026-01-01)


### Build System

* **backend:** add build extra dependency and update hatch usage ([cb376a4](https://github.com/Pushikoo/Pushikoo/commit/cb376a4d0b0cce5f38989032254122f1ef15d88d))

## [0.10.0](https://github.com/Pushikoo/Pushikoo/compare/v0.9.0...v0.10.0) (2026-01-01)


### Features

* add cron expression editor component with preset and custom modes ([2c435ee](https://github.com/Pushikoo/Pushikoo/commit/2c435ee5055c1f9ff7bb8adad6922d8295e4d5de))
* add version display in backend startup and frontend sidebar ([d01cfd9](https://github.com/Pushikoo/Pushikoo/commit/d01cfd91fda083f521347e5cf0776ae3ceb949e1))

## [0.9.0](https://github.com/Pushikoo/Pushikoo/compare/v0.8.1...v0.9.0) (2026-01-01)


### Features

* **pip:** prefer uv over pip when available ([7177fd2](https://github.com/Pushikoo/Pushikoo/commit/7177fd231a9cf6b43c9051c59324401afec0290d))
* **ui:** sort adapters by type priority and name ([9316f7b](https://github.com/Pushikoo/Pushikoo/commit/9316f7b7a217054994a9eed78c1514d76ee7b89e))

## [0.8.1](https://github.com/Pushikoo/Pushikoo/compare/v0.8.0...v0.8.1) (2025-12-28)


### Bug Fixes

* adapter updates not taking effect after install/uninstall ([2e3e4da](https://github.com/Pushikoo/Pushikoo/commit/2e3e4dac3d349af0ae0bf61a86cb8184c58fa8e3))

## [0.8.0](https://github.com/Pushikoo/Pushikoo/compare/v0.7.1...v0.8.0) (2025-12-28)


### Features

* **flows:** improve drag-and-drop styling for flow nodes ([1634f82](https://github.com/Pushikoo/Pushikoo/commit/1634f8232f41799751e14863f9b1d3028f4f9cae))


### Performance Improvements

* **vite:** add optimizeDeps configuration for better performance ([4a993db](https://github.com/Pushikoo/Pushikoo/commit/4a993dbb40157607a83d67c9570f0d5fe1977114))

## [0.7.1](https://github.com/Pushikoo/Pushikoo/compare/v0.7.0...v0.7.1) (2025-12-23)


### Bug Fixes

* **deps:** adapter version not updated after installing a new version ([0dd8a6c](https://github.com/Pushikoo/Pushikoo/commit/0dd8a6c1b303516fddf11c25576fc01b8a21c38d))

## [0.7.0](https://github.com/Pushikoo/Pushikoo/compare/v0.6.0...v0.7.0) (2025-12-22)


### Features

* add ImageService for image storage and access links ([efe06af](https://github.com/Pushikoo/Pushikoo/commit/efe06af9105e5f955f9e8bdbd8ea462098f50748))
* **frontend:** add Struct markdown renderer for consistent message preview ([d9c52df](https://github.com/Pushikoo/Pushikoo/commit/d9c52dfd65d2c8b6a405d23cd2dc76b12304fe7e))
* **frontend:** enhance image preview in messages page ([12991c0](https://github.com/Pushikoo/Pushikoo/commit/12991c0bd0a2735f807ddb970985e58a9cf68685))
* **messages:** improve image scaling logic for better fit within container ([d8df41c](https://github.com/Pushikoo/Pushikoo/commit/d8df41c255eb61d7b09ad03372d36b4e92163851))


### Documentation

* simplify prerequisites by removing Python version requirement ([30b8f6a](https://github.com/Pushikoo/Pushikoo/commit/30b8f6af0ae1484eae3f758dbe134f7ca423da4d))

## [0.6.0](https://github.com/Pushikoo/Pushikoo/compare/v0.5.1...v0.6.0) (2025-12-21)


### Features

* **setting:** Updated .env.example to set default ENVIRONMENT to production and ([27c0ab5](https://github.com/Pushikoo/Pushikoo/commit/27c0ab5520d3b3cf507e69b1e48000cbc75e5415))


### Documentation

* **readme:** add environment variable configuration guide ([27c0ab5](https://github.com/Pushikoo/Pushikoo/commit/27c0ab5520d3b3cf507e69b1e48000cbc75e5415))

## [0.5.1](https://github.com/Pushikoo/Pushikoo/compare/v0.5.0...v0.5.1) (2025-12-20)


### Bug Fixes

* add type assertion for v-for index in SchemaForm tuple loop ([df5f4bd](https://github.com/Pushikoo/Pushikoo/commit/df5f4bd3ba87acd2bf7bc70d9db88ea0b6390498))

## [0.5.0](https://github.com/Pushikoo/Pushikoo/compare/v0.4.0...v0.5.0) (2025-12-20)


### Features

* simulate venv activation on startup for bare command support ([f20ea19](https://github.com/Pushikoo/Pushikoo/commit/f20ea195c6c31d4e240b47caba951e4859fcbf5b))

## [0.4.0](https://github.com/Pushikoo/Pushikoo/compare/v0.3.0...v0.4.0) (2025-12-20)

### Features

- **frontend:** improve mobile responsiveness for all pages ([fa53a67](https://github.com/Pushikoo/Pushikoo/commit/fa53a672a5b4dd41b91fd037a3a8b57d349f9c00))

## [0.3.0](https://github.com/Pushikoo/Pushikoo/compare/v0.2.3...v0.3.0) (2025-12-19)

### Features

- **flows:** change Execute dialog from exclude to include node selection ([1549169](https://github.com/Pushikoo/Pushikoo/commit/15491696dad22afb39c9cef628db95bbb7b8618e))

### Documentation

- add comprehensive README with Chinese and Japanese translations ([7c6727a](https://github.com/Pushikoo/Pushikoo/commit/7c6727ab7233ad09ea9e10f183b436f727b1cc8e))

## [0.2.3](https://github.com/Pushikoo/Pushikoo/compare/pushikoo-v0.2.2...pushikoo-v0.2.3) (2025-12-19)

### Bug Fixes

- **cron:** edit ineffective ([8bef3f4](https://github.com/Pushikoo/Pushikoo/commit/8bef3f407303305d1fbb34b031d4a35e9a9d7256))

## [0.2.2](https://github.com/Pushikoo/Pushikoo/compare/pushikoo-v0.2.1...pushikoo-v0.2.2) (2025-12-19)

### Bug Fixes

- **api:** replace get_object_by_id with get() in instance API ([9711721](https://github.com/Pushikoo/Pushikoo/commit/9711721980dbb2761ee02a17b6427d95479b99bb))

## [0.2.1](https://github.com/Pushikoo/Pushikoo/compare/pushikoo-v0.2.0...pushikoo-v0.2.1) (2025-12-19)

### Continuous Integration

- update release-please workflow outputs and versioning setup ([3c5f08d](https://github.com/Pushikoo/Pushikoo/commit/3c5f08defac740adf0b45b2b2485482949ce0359))
