# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-01-XX

### 🚀 Major Features

- **Agent API v2 Implementation**: Introduced the modernized Agent API v2 with enhanced features and improved security
  - Enhanced authentication with improved token security and expiration support
  - Better state management using finite state machine implementation for agent lifecycle
  - Improved resource management with time-limited presigned URLs and hash verification
  - Enhanced error handling with structured responses and proper HTTP status codes
  - Rate limiting infrastructure with comprehensive headers and backoff strategies
  - Forward-compatible design for Phase 3 resource management

### 🏗️ Architecture

- **Multi-API Structure**: Established clear separation between Agent API v1 (legacy), Agent API v2 (modern), Web UI API, and Control API
- **Routing Infrastructure**: Created modular endpoint organization under `app/api/v2/endpoints/`
- **Backward Compatibility**: Maintained full compatibility with existing v1 agents while introducing v2 enhancements

### 📚 Documentation

- **Comprehensive API Documentation**: Added detailed Agent API v2 documentation with examples and migration guides
- **Development Guide**: Created comprehensive development guide for Agent API v2 implementation
- **Architecture Updates**: Updated API architecture documentation to reflect multi-version support

### 🔧 Technical Improvements

- **Version Bump**: Updated project version to 2.0.0 reflecting major API enhancements
- **Dependency Updates**: Updated core dependencies including FastAPI, Pydantic, and SQLAlchemy
- **Testing Infrastructure**: Established testing framework for v2 API validation and contract testing

### 🚧 Development Status

- **Foundation Complete**: Core routing, authentication framework, and error handling infrastructure implemented
- **Endpoints Planned**: Agent registration, heartbeat, task management, and resource access endpoints designed
- **Future Implementation**: Full v2 API functionality planned for upcoming releases

### 📖 Migration

- **Dual API Support**: v1 and v2 APIs can run simultaneously without conflicts
- **No Breaking Changes**: Existing v1 agents continue to work unchanged
- **Migration Path**: Clear upgrade path provided for agents to adopt v2 features

## [0.6.6] - 2024-12-22

### 🚀 Features

- Add .erb-lint.yml configuration for custom linting

Introduce a new .erb-lint.yml file to configure ERB linters. Default linters are disabled, and Rubocop is selectively enabled with specific exclusions and overrides. This configuration integrates with an existing .rubocop.yml file for consistency.

### 🚜 Refactor

- Simplify comments and documentation across app

Removed verbose and redundant inline comments from multiple files to improve readability. Focused on essential descriptions for methods, modules, and classes while maintaining clarity and functionality.

### 📚 Documentation

- Add schema information to model comments

Add detailed schema information to all models for better clarity
and reference. This will help developers understand the database
structure directly from the model files.

### ⚙️ Miscellaneous Tasks

- Update Ruby version to 3.3.6 and bump dependencies

Aligned the Ruby version to 3.3.6 across `.ruby-version`, `Gemfile`, and `Dockerfile`. Updated dependencies in `Gemfile.lock` to their latest compatible versions, improving stability and compatibility. Verified compliance with project constraints and ensured CI consistency.

## [0.6.5] - 2024-10-23

### 🚀 Features

- Remove Bootswatch stylesheets and add MPL-2.0 licenses

Removed Bootswatch SCSS stylesheets from the project. Added SPDX license headers to various Ruby and config files for MPL-2.0 compliance.

- Implement filter to restrict task assignment based on agent benchmark performance ([#199](https://github.com/unclesp1d3r/ouroboros/issues/199))

### 🐛 Bug Fixes

- Correct transition trigger for attack model

Changed the transition trigger from :running to :run in the attack model. This ensures the start_time and campaign touch operations are executed correctly.

- Add ability to override machine name ([#197](https://github.com/unclesp1d3r/ouroboros/issues/197))

### 🚜 Refactor

- Add functionality to reupload and reingest hash lists ([#195](https://github.com/unclesp1d3r/ouroboros/issues/195))

- Delegate hash_mode method to hash_list

Replaces the hash_type method with a delegate call to the hash_list's hash_mode method. This change simplifies the code by removing the redundant hash_type method and directly delegating to hash_list.

- Switch changelog tool to git-cliff

Removed .chglog configuration files and replaced with git-cliff configuration by adding cliff.toml. This change simplifies the changelog generation process and uses git-cliff's templating and commit parsing capabilities.

### 📚 Documentation

- Update CHANGELOG for v0.6.4 release

Update the CHANGELOG.md to reflect changes for the v0.6.4 release, including new features, refactoring, and documentation improvements. Notable updates cover HTTP caching, an after_transition hook, and enhancements to task and attack management.

- Add Table of Contents and Improve Readability in README

Introduce a detailed Table of Contents to enhance navigation. Reformat sections for better readability and relocate "Project Assumptions and Target Audience" for logical flow. Improved inline code blocks for setup instructions.

### 🧪 Testing

- Correct usage of change matcher in hash list spec

Update hash_lists_spec.rb to properly use the change matcher syntax. This ensures that the test accurately checks if the 'processed' attribute changes from true to false after updating the hash list.

### ⚙️ Miscellaneous Tasks

- Remove commented out SCSS imports

Removed commented out imports from the SCSS file to clean up the code. This change helps in improving readability and maintenance of the stylesheet.

- Improve changelog configuration

Added sorting by date and updated commit group titles with emojis for better readability. Changed the sorting logic within commit groups to title-based and updated the filter types.

- Update dependencies in yarn.lock and Gemfile.lock

Upgrade various dependencies in yarn.lock and Gemfile.lock to their latest versions. This includes updates to caniuse-lite, electron-to-chromium, sass, and several Ruby gems like aws-partitions and groupdate.

- Merge develop changes into main ([#200](https://github.com/unclesp1d3r/ouroboros/issues/200))

- Update changelog for version 0.6.5

Update the changelog to reflect the new version 0.6.5 release. The update includes a switch from .chglog to git-cliff for changelog generation.

## [0.6.4] - 2024-09-26

### 🚀 Features

- Add after_transition hook for resume event

This commit adds an after_transition hook to the Task model for the resume event. When a task transitions to the resume state, it now updates the task to set the stale attribute to true. This ensures tasks marked as resumed are properly flagged as stale.

- Add caching with fresh_when to controllers

This commit adds fresh_when to hash_lists and campaigns controllers. This enables HTTP caching, improving performance and reducing redundant data delivery to clients.

### 🚜 Refactor

- Streamline attack stepper rendering

Replace inline attack rendering with collection rendering in the campaign show view. Adjust attack stepper partial to integrate with the new stepper methodology, improving code readability and maintainability.

- Restructure and optimize task management

Extract methods for checking agent status, removing task statuses, and abandoning tasks into private methods. Ensure database connections are properly cleared after execution.

### 📚 Documentation

- Add detailed documentation for Campaign model

Added comprehensive class-level and method documentation for the Campaign model. This includes explanations of priorities, state transitions, associations, and method functionalities to enhance code readability and maintainability.

- Simplify and restructure Attack model documentation

Refactored the documentation for the Attack model by removing unnecessary details and organizing it for better readability. Improved the structure by grouping related sections and adding concise explanations to methods and state transitions.

- Update CHANGELOG for v0.6.4 release

Include documentation for new features, refactoring efforts, and improved documentation for models. Notable changes include HTTP caching, the addition of an after_transition hook, and restructuring of task and attack management code.

### ⚙️ Miscellaneous Tasks

- Update dependency versions in lock files

Upgraded various package versions in yarn.lock and Gemfile.lock for improved compatibility and security. Notable updates include browserslist to 4.24.0, caniuse-lite to 1.0.30001663, and aws-sdk-core to 3.209.1.

- Pause lower priority campaigns during status update

Add functionality to pause lower-priority campaigns within the `UpdateStatusJob` job. This ensures that resources are allocated more efficiently and higher priority tasks receive the necessary attention.

## [0.6.3] - 2024-09-24

### 🚀 Features

- Add toggle for hiding completed activities

Implemented a toggle button for users to hide or show completed activities in campaigns and attacks. Updated the user model and routes to support this feature and enhanced the UI with the necessary components.

- Add delete button with confirmation to item list

Introduce a delete option for items in the list with a confirmation prompt to ensure the user intends to delete the item. This adds an additional layer of security to prevent accidental deletions.

- Move toggle visibility feature to campaigns controller

Replaced the toggle hide completed activities functionality from the home controller to the campaigns controller. Updated routes and views accordingly to reflect this change, improving feature organization and routing logic consistency.

### 🐛 Bug Fixes

- Remove deprecated browser version check

Removed the `allow_browser` method, which checked for modern browser versions. This simplifies the application controller and ensures compatibility with the latest browser capability checks.

### 🚜 Refactor

- Optimize agent views and improve authorization

Refactored agent views to use partial rendering and caching for efficiency. Updated the authorization logic to include Task management permissions. This improves both code maintainability and performance.

- Extract user and project rows into partials

Refactored admin index view to use partials for user and project rows. This change improves code readability and reusability. Added caching for partials to enhance performance.

- Simplify layout and make navbar persistent

Replaced individual Turbo tags with a combined method for clarity. Ensured the navbar retains its state with `data-turbo-permanent` attribute.

- Streamline hash list rendering in views

Simplify rendering of hash lists by using a partial in the index view. Consolidate the logic of individual hash list items and use Turbo Streams for dynamic content updates.

### 🎨 Styling

- Standardize Dockerfile stage names to uppercase aliases

Ensure consistent capitalization for Dockerfile AS stage names for clarity and readability. This change does not affect functionality but helps maintain a uniform style across the Dockerfile.

### ⚙️ Miscellaneous Tasks

- Remove unused resource limits and replicas in docker

This commit removes the resource limits and replicas definitions from docker-compose.yml, as they were not being used effectively. The removal simplifies the configuration and reduces potential confusion related to resource management in the Docker setup.

- Add SQL dialect config and update CI workflow

Added .idea/sqldialects.xml to specify PostgreSQL dialect for the project. Updated CI.yml to use DATABASE_URL environment variable for the test database configuration.

- Add wget package to Docker setup

Updated the Dockerfile and dockerfile.yml configuration to include the wget package. This addition ensures wget is available in the Docker environment for network operations.

- Update database environment variable in CI config

Replace DB_HOST with DATABASE_URL for CircleCI test environment. This change ensures the correct database connection string is used during CI builds.

- Upgrade package versions in yarn.lock and Gemfile.lock

Upgraded several dependencies in both yarn.lock and Gemfile.lock files. Updated caniuse-lite, active_storage_validations, and multiple AWS SDK components to their latest versions to ensure compatibility and security.

- Update CHANGELOG for v0.6.3 release

Include features like delete button for items, toggle for hiding completed activities, and refactorings for views and layout. Also note style changes and bug fixes for deprecated browser checks.

- Updated CHANGELOG.md

## [0.6.2] - 2024-09-23

### 🚀 Features

- Enhance docker-compose for production deployments

Updated healthchecks for services to use HTTP checks and added resource constraints and deployment configuration for better resource management and reliability. Introduced `sidekiq_alive` gem for improved Sidekiq monitoring and updated various dependencies to their latest versions.

- Implement caching to improve performance

Added Rails caching to multiple methods and queries to reduce database load and improve application performance. Introduced Redis as the cache store in the production environment for enhanced caching support.

- Update status pill indicator for running status

Replace status icon with a spinner for "running" status. This change enhances visual feedback by showing an animated indicator instead of a static icon when the status is "running".

- Display current running attack on agent show page

Add logic to display a link to the current running attack on the agent's show page. This includes a new method in the Agent model to retrieve the current running attack, if any.

- Add progress tracking and enhance status display

Introduce methods to track current iteration, device speed, and progress percentages in the Attack and HashcatStatus models. Updated the Task, Campaign, and view files to utilize these new methods, providing more detailed and organized information about attack progress and status.

- Add PWA support and update browser handling

Introduce PWA support with new service worker and manifest files. Update routes and asset files to accommodate PWA requirements. Modify CSS and add browser version handling in application controller.

### 🐛 Bug Fixes

- Use after_commit instead of after_save for update_line_count

Changed the callback from after_save to after_commit to ensure update_line_count is called only after the transaction is committed. This prevents potential issues with partially completed transactions affecting the line count update.

- Reduce retry attempts and log line count

Reduced retry attempts for ActiveStorage::FileNotFoundError to minimize job delays. Added logging of line count to help monitor job execution and file processing.

- Remove touch option and modify callbacks and methods

The `touch` option was removed from the `belongs_to :campaign` association. The `after_create` callback was updated to `after_create_commit`. The `update_stored_complexity` method now updates the record directly, and the `force_complexity_update` method no longer calls `save`.

- Correct complexity_value comparison

Changed the comparison method for complexity_value to ensure it accurately checks for zero values as a float instead of an integer. This should prevent potential issues related to type mismatches during the comparison.

- Ensure campaign timestamp updates on hash cracking

Add touch method to campaign when a hash is cracked to update the campaign's timestamp. This change avoids potential issues with outdated campaign state information.

### 🚜 Refactor

- Extract attack stepper line into partial

Moved attack stepper line rendering logic to a partial. This change improves readability and makes the code easier to maintain by encapsulating repeated components.

- Update campaign table for improved responsiveness

Changed the table class to 'table-sm' for better mobile view compatibility. Realigned the indentation for better code readability. This improves the presentation and maintainability of the campaigns list.

- Optimize database migrations for hash_items and agents

Apply bulk changes in database migrations for hash_items and agents tables. This improvement uses the change_table method, streamlining the removal and addition of columns.

### ⚙️ Miscellaneous Tasks

- Delete .idea/sqldialects.xml

Remove obsolete IDE configuration file. This cleanup helps in maintaining a cleaner repository by eliminating unnecessary project-specific settings.

- Enhance docker setup and optimize build process

Simplified .dockerignore patterns and centralized docker-compose resources and environment variables. Modularized Dockerfile build stages for better caching and added parallel setup option in config/dockerfile.yml.

- Update dependencies and clean up Gemfile and .gitignore

Updated various dependencies in yarn.lock and Gemfile.lock, including chokidar, electron-to-chromium, nodemon, sass, and turbo-rails. Removed spring and rack-mini-profiler from the Gemfile. Also cleaned up .gitignore and adjusted the require statement for the debug gem.

- Remove changelog file

Deleted changelog.yml to simplify repository structure. This file was moved to alternative documentation methods.

- Update CHANGELOG for v0.6.2 release

Add detailed entries for new features, refactoring, and bug fixes in version 0.6.2. Highlights include PWA support, progress tracking enhancements, and various improvements in performance and code readability.

## [0.6.1] - 2024-09-20

### ⚙️ Miscellaneous Tasks

- Fixed deployment issues discovered in 0.6.0 ([#186](https://github.com/unclesp1d3r/ouroboros/issues/186))

## [0.6.0] - 2024-09-19

### 🚀 Features

- Added a blank slate component

I added a blank slate component to all the index pages to show when there is nothing and instruct the user to add an item. I also cleaned up the loading of associated resources in the view files by moving them into the controller and making them more reliable.

- Upgraded to Rails 7.2

- Attacks are now sorted by their complexity

We did significant refactoring across the entire application, including adding comments to nearly every class to make it easier to understand and enhance IDE’s understanding of the objects. We also calculated how complex an attack and the various attack resources might be so that we could automatically sort attacks with the easiest ones first. I’m sure I missed something in the calculation, but it’s a start.

- Add priority to campaigns

Introduced a priority enum to the Campaign model, with updated DB schema and associated logic. Enhanced CampaignsController to handle the new priority attribute and extended the Campaign model with new methods and callbacks for priority management.

### 🐛 Bug Fixes

- Fixed an issue with the activity feed erroring when a mask list was running

- SubmitAgentError no longer generates a cascading error if task isn’t found

- Resolved a weird bug breaking the docker builds

- Resolved a minor issue with shared masks not showing up in the attack editor

- Added tests and improvements to Project and Agent access control

We are implementing more granular control over abilities within the system, based not just on whether the user is an admin but also on their permissions on the projects associated with the resources. This cleanup effort involves writing controller tests to verify that permissions are working and fixing any situations where the tests fail. We started with the resources that aren’t children of projects.

- Updated the count file lines job to simplify it.

The job was unnecessarily complex and did not always function reliably if something glitched. I simplified it to improve reliability and updated it to work with RSpec 7.

- Simplified the permissions structure and added extensive tests

We were initially planning on having numerous roles per project, with different user levels having different capabilities, but that proved more complicated than it was worth. We removed all that, so any project member can manage anything within the project, but only a site admin can manage shared items. We then wrote extensive RSpec tests to validate this.

- Fixed a 500 error on the activities page when there are no tasks for an attack

- Add set_projects before_action for new/edit/create/update

Add a before_action to set accessible projects in both WordLists and RuleLists controllers. This ensures that project data is available for these actions, improving code consistency and maintainability.

- Display status for unprocessed line counts

Previously, line counts were always shown even if they were not processed. Now, the view renders "pending" for items that haven't been processed, improving clarity for users.

- Ensure proper error handling and task updates

Corrected error handling in task acceptance and alignment issues. Enhanced task update logic to prevent stale state overlap by excluding affected task IDs.

- Correct typos and streamline HTML elements

Corrected a spelling error in the campaign model's comments and streamlined the table row ID and iteration syntax in the campaign and attack partials for better readability and consistency.

- Update schema and add task completion checks

Renamed agent's 'active' field to 'enabled' and updated related comments in the schema. Added `mark_attacks_complete` callback in Campaign model to manage the task completion process dynamically. Refined task assignment logic in the Agent model to enhance performance and reliability.

### 🚜 Refactor

- Merged updates from issue 47

- Rename agent field `active` to `enabled`

Renamed the `active` field to `enabled` in the `Agent` model for better clarity. Updated associated views, tests, and database schema migration accordingly.

- Correct typo in priority enum comment

Fixed a typo in the campaign priority enum comment within the migration. Changed 'Defered' to 'Deferred' to ensure accurate documentation.

### ⚙️ Miscellaneous Tasks

- Updated CHANGELOG

- Minor reordering of the Gemspec file

- Added railsboot vendor code to CodeClimate exclude

Since it is vendor content, it shouldn’t weigh against our score on CodeClimate, so I’m excluding the RailsBootUI components.

- Minor formatting changes

- Regenerated devcontainer with Rails 7.2

- Updated version of Ruby to 3.3.5

- Added newer annotaterb gem instead of annotate

- Updated dev container to include VS Code plugins

- Update dependencies in Gemfile.lock and yarn.lock

This commit updates several dependencies in the Gemfile.lock and yarn.lock files to their latest versions. These include `aws-partitions`, `aws-sdk-s3`, `turbo-rails`, `@hotwired/turbo-rails`, and other related packages. The updates aim to keep the project dependencies current and secure.

- Update docker-compose and remove sidekiq-worker

Remove sidekiq-worker service from both docker-compose and production configurations, and add Redis volume configuration and health check. Adjust replication and restart policy settings for increased reliability and streamlined service management.

- Disable RbsMissingTypeSignature inspection tool

The RbsMissingTypeSignature inspection tool has been disabled in the project settings. This change sets the tool's warning level to WEAK WARNING and ensures it is not enabled by default.

- Updated CHANGELOG.md

- Update Ruby image and improve CI configuration

Upgrade Ruby Docker image to 3.3.5 in CircleCI config. Add PostgreSQL service and database setup steps in GitHub Actions workflow to ensure consistency checks run smoothly.

- Remove database_consistency gem and related configs

Deleted the database_consistency gem from Gemfile and removed its configurations. This includes deleting the .database_consistency.todo.yml file and removing related checks in the CI workflow. Also updated Gemfile.lock accordingly.

## [0.5.4] - 2024-09-03

### 🐛 Bug Fixes

- Added rexml dependency

### ⚙️ Miscellaneous Tasks

- Updated changelog

## [0.5.3-001] - 2024-09-03

### 🚀 Features

- Upgraded ruby and rails versions ([#181](https://github.com/unclesp1d3r/ouroboros/issues/181))

### 📚 Documentation

- Updated changelog format to include comments

We use an automatic changelog generator (git-chglog) and often include comment bodies to explain a change in our commits further. This update to the configuration will now include those explanations.

### 🧪 Testing

- Added basic controller tests and cleaned up identified issues

I created bare stubs that test each controller action that is accessible via HTTP GET. This revealed a few routes that were either wholly unneeded or severely broken. I will continue adding more tests to flesh out the permissions model as I lock down some of the features to different roles.

### ⚙️ Miscellaneous Tasks

- Update .gitattributes ([#180](https://github.com/unclesp1d3r/ouroboros/issues/180))

Changed gitattributes to always use crlf, since we use dev containers on windows, so it should always be consistent with Unix formats.

## [0.5.3] - 2024-08-29

### 🚀 Features

- Updating an attack now resets it and makes it available

### 🐛 Bug Fixes

- Resolved issue preventing the pause button from functioning

### ⚙️ Miscellaneous Tasks

- Updated CHANGELOG

## [0.5.1-001] - 2024-08-27

### 🐛 Bug Fixes

- Fixed major bug preventing creation of new campaigns

- Added cascade on foreign keys to remove children of hash lists if hash lists are deleted

### ⚙️ Miscellaneous Tasks

- Minor reordering of the Gemspec file

## [0.5.1] - 2024-08-26

### 🐛 Bug Fixes

- Fixed an issue with the activity feed erroring when a mask list was running

- SubmitAgentError no longer generates a cascading error if task isn’t found

- Resolved a weird bug breaking the docker builds

### ⚙️ Miscellaneous Tasks

- Updated CHANGELOG

## [0.5] - 2024-08-26

### 🚀 Features

- Added support for mask lists on mask attacks

This allows files containing mask attacks to be attached in hcmask format.

BREAKING CHANGE

- Added soft deletion to attacks and campaigns

- Simplified attacks to only allow one each of resource files

The attack logic was becoming incredibly unwieldy because we were supporting combinator attacks. Every other attack type allows a single word list, rule list, or mask list. Support for combinators broke the UI and made the data structures more complex. We removed combinators and recommend just precalculating the combinator attacks as word lists.

- Major improvements in visual consistency and UI

### 🐛 Bug Fixes

- Invalid benchmarks no longer block updates

- Fix blank users being created

- Agents only re-benchmark if they have no benchmarks

- Removed constraint on duplicate hashes

There was a weird bug where the hash item would get created as a duplicate but could never be updated or cracked because it didn’t meet validation. While fixing this, I realized that we might actually want duplicate hashes because there may be multiple users with the same password in a dump, and the metadata would differentiate them.

### 🚜 Refactor

- DRY’d up the attack resources and fixed the attack validations

- Minor cleanup of erb files

### 📚 Documentation

- Grammer-checked the primary project documents

### ⚙️ Miscellaneous Tasks

- Updated the Gemfile.lock to reflect the removed gem

- Bumped yarn packages

- Updated CHANGELOG

## [0.4.2] - 2024-08-07

### 🚀 Features

- Agents are now notified if there’s new cracks or the task is paused

### 🐛 Bug Fixes

- Significantly improved standardization of the API

I made quite a few refactors to the agent API, but it is a significant breaking change.

MAJOR BREAKING CHANGE

- Tasks are no longer stale when the zaps are downloaded

- Refactor of API to 1.4 to make it more standardized. ([#168](https://github.com/unclesp1d3r/ouroboros/issues/168))

- Fixed issue with benchmarks not being submitted correctly

For some reason, it only seemed to show up once we moved to benchmarking everything. Now, it is more resilient to write errors.

### ⚙️ Miscellaneous Tasks

- Enabled the CI actions on the develop branch

- Updated changelog

- Delete backup files created in last merge

- Corrected issue with method order

This was a minor issue caused by the Rubocop-ordered methods check. I missed one of the API methods, but it did not break anything except the CI pipeline’s checks.

## [0.4.1] - 2024-08-01

### 🐛 Bug Fixes

- Removed unused agent properties

We added several properties to smooth the transition from Hashtopolis, but they didn’t make sense for Ouroboros’s use case. We have removed them to clean up the functionality.

- Changed the agent benchmarks to aggregate benchmarks

For systems with multiple GPUs, the benchmark listing showed the speed of each GPU for the various hashes. While this might be useful for some, it was confusing and messy for most. It now adds the speeds of all GPUs for each hash, which more accurately reflects how Hashcat would use them.

### 📚 Documentation

- Removed FOSSA scan that never really worked

### 🧪 Testing

- Restored test for ordered methods

We used to test whether methods were in alphabetical order, but the Rubocop plugin that did that broke. Now that it’s working again, we are testing it again.

### ⚙️ Miscellaneous Tasks

- Updated changelog

## [0.4] - 2024-07-29

### 🚀 Features

- Agents are now notified if there’s new cracks or the task is paused

### ⚙️ Miscellaneous Tasks

- Enabled the CI actions on the develop branch

- Updated changelog

## [0.3.4] - 2024-07-24

### 🚀 Features

- Added ability to pause campaigns

### 🐛 Bug Fixes

- Added text to confirm tasks are deleted with attacks

- Made line_count larger on Rule and Word Lists

- Allow longer hash values

- Hash list ingest now handles duplicate values correctly

- Completing the hash list now completes the campaign

### ⚙️ Miscellaneous Tasks

- Bumped dependencies

- Updated docker-compose-production to support swarm

- Disabled broken rubocop-ordered_methods

- Updated change log

## [0.3.3-20240622] - 2024-06-22

### 🐛 Bug Fixes

- Improved job queues fo high volume system

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG

## [0.3.3] - 2024-06-21

### 🚀 Features

- Improved Large File Upload

The upload forms now use direct upload using Javascript to significantly improve performance and handle extremely large files.

- Benchmark speed is now show in SI units

### 🐛 Bug Fixes

- Clean up excessive hashcat statuses

The status count can now be configured as task_status_limit, which defaults to 10. All running tasks will only keep 10 status, all completed tasks keep no status.

- Jobs now retry 3 times when a record is not found

This fixes an issue with a hash, word, or rules list being deleted before it was fully ingested and the processing job just continually trying forever.

- Word and Rule Lists now require a project if marked sensitive

- Removed duplicate notifications on index pages

### ⚙️ Miscellaneous Tasks

- Updated ChangeLog

## [0.3.2] - 2024-06-18

### 🚀 Features

- Added support for sending OpenCL device limits

## [0.3.1] - 2024-06-17

### 🐛 Bug Fixes

- Fixed minor bugs preventing deployment in docker

- Fix issue with font broken on isolated network

The theme we were using was trying to reach out to google fonts API and was causing the turbo refreshes to hang. Just switched back to the default bootstrap theme until we move to flowbite.

- Standardized the titles of pages

- Fixed issue with view hash list permission

### ⚙️ Miscellaneous Tasks

- Updated changelog

## [0.3.0-20240617] - 2024-06-16

### 🐛 Bug Fixes

- Included master.key in docker container

## [0.3.0-20240616] - 2024-06-16

### 🐛 Bug Fixes

- Included master.key to fix deployment

We don't use any encrypted credentials, so there's no reason not to just include it. IF you publish your ouroboros server publicly, you should change the master.key and the contents of the of the credentials

## [0.3.0] - 2024-06-14

### 🚀 Features

- Exposed agent advanced configuration

- Update Agent to show errors and benchmarks

Also added support for enabling additional benchmark types, which will allow the agent to be used for those hash types

- Add bidirectional status on heartbeat

Added a state to the agent that can be toggled. This removes the agent’s responsibility to determine if it needs to run benchmarks, it should check for a 200 return on heartbeat and look for a status of ‘pending’. Otherwise, it can get it on start up when it gets its agent data.

BREAKING CHANGE

### 🐛 Bug Fixes

- Minor form cleanup on hash lists and rules

- Fixed rule list link

- Agents shutting down now abandon their tasks

- Fix benchmark false positive

### 🚜 Refactor

- Changed unprocessable_entity to unprocessable_content

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG

- Update docker deploy action

## [0.2.6] - 2024-06-12

### 🚀 Features

- Exposed agent advanced configuration

- Update Agent to show errors and benchmarks

Also added support for enabling additional benchmark types, which will allow the agent to be used for those hash types

- Add bidirectional status on heartbeat

Added a state to the agent that can be toggled. This removes the agent’s responsibility to determine if it needs to run benchmarks, it should check for a 200 return on heartbeat and look for a status of ‘pending’. Otherwise, it can get it on start up when it gets its agent data.

BREAKING CHANGE

### 🐛 Bug Fixes

- Fixed rule list link

### 🚜 Refactor

- Changed unprocessable_entity to unprocessable_content

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG

- Update docker deploy action

## [0.2.5] - 2024-06-11

### 🐛 Bug Fixes

- Minor form cleanup on hash lists and rules

## [0.2.4] - 2024-06-07

### 🚀 Features

- Exposed agent advanced configuration

- Update Agent to show errors and benchmarks

Also added support for enabling additional benchmark types, which will allow the agent to be used for those hash types

- Add bidirectional status on heartbeat

Added a state to the agent that can be toggled. This removes the agent’s responsibility to determine if it needs to run benchmarks, it should check for a 200 return on heartbeat and look for a status of ‘pending’. Otherwise, it can get it on start up when it gets its agent data.

BREAKING CHANGE

### 🐛 Bug Fixes

- Add better logic for empty metadata in errors

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG

## [0.2.2] - 2024-06-02

### 🐛 Bug Fixes

- Fix incorrect AgentError severity enum

The enum had an extra comma at the end of each word that shouldn’t have been there.

## [0.2.1] - 2024-06-02

### 🚀 Features

- Add minio backend storage

- Add Lazy Preloading throughout the app

This should reduce the risk of N+1 queries.

- Add API for collecting agent errors

### 🐛 Bug Fixes

- Fix progress bar calculating

The tasks were showing the wrong progress due to a math issue.

- Remove broken viewcomponent generator

### 🚜 Refactor

- Rename api operations to be more consistent

BREAKING CHANGE

Renamed the various api endpoints to be more consistent with verbNoun in camelCase.

- Standardize API names ([#103](https://github.com/unclesp1d3r/ouroboros/issues/103))

- Add ViewComponentContrib

- Add additional database rules

### 📚 Documentation

- Update changelog with v0.1.6

- Add contribution documents

Added contributing instructions explaining the use of our coding standards. Also added a Code of Conduct.

- Update README and Changelog

- Updated annotations

### 🎨 Styling

- Remove Rails/ReversibleMigration cop

### ⚙️ Miscellaneous Tasks

- Reduce frequency of dependabot checks

- Add database consistency test

## [0.1.6] - 2024-05-21

### 🚀 Features

- Add ability to change password ([#97](https://github.com/unclesp1d3r/ouroboros/issues/97))

Logged in users can now change their password by selecting from the user menu on the right of the menubar

### 🚜 Refactor

- Add additional conventions to chglog

### 📚 Documentation

- Add note about conventional commits

- Tried to improve changelog

## [0.1.0] - 2024-04-30

<!-- generated by git-cliff -->
