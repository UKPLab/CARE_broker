# Broker Changelog

## v.0.3.0 - 2023-12-22

### Added

- Command line interface (User management and model deployment)
- Model deployment per command line (openai azure api, llama.cpp, huggingface pipeline, vader)
- Data consent (donation of data in task requests)
- NoSQL database (ArangoDB) for caching and storing task requests
- Role based access control (RBAC) for users
- Support for task status updates
- Support for task cancellation
- Basic examples for skill and client (Jupyter Notebook)

### Changed

- User group based quota

### Fixed

- Try/Catch blocks for all requests
- Cleaned up and improved build process

## v.0.2.0 - 2023-04-25

### Added

- Added quota (for all requests)
- Basic unittests for the broker

### Changed

- Removed token verification

## v.0.1.0 - 2023-02-24

Initial release of the broker.