# Requirements Document

## Introduction

This specification defines the requirements for implementing a NiceGUI-based web interface integrated directly into the CipherSwarm FastAPI backend application. This alternative web interface will replicate the functionality and layout of the existing SvelteKit frontend while being served directly from the FastAPI application, eliminating the need for a separate frontend server and providing a more integrated deployment option.

The NiceGUI interface will provide the same core functionality as the SvelteKit frontend but with a Python-native implementation that can be more easily customized and extended by backend developers.

## Requirements

### Requirement 1: Core Application Structure

**User Story:** As a system administrator, I want a NiceGUI web interface integrated into the FastAPI backend, so that I can deploy a single application without managing separate frontend and backend services.

#### Acceptance Criteria

1. WHEN the FastAPI application starts THEN the NiceGUI interface SHALL be available at `/ui/` path
2. WHEN a user accesses `/ui/` THEN the system SHALL serve the NiceGUI-based dashboard
3. WHEN the application is deployed THEN it SHALL require only the FastAPI backend container
4. IF the user accesses `/ui` without trailing slash THEN the system SHALL redirect to `/ui/`
5. WHEN the NiceGUI interface is active THEN it SHALL use the same authentication system as the existing APIs

### Requirement 2: Dashboard Interface

**User Story:** As a user, I want a dashboard that displays system metrics and campaign overviews, so that I can quickly assess the current state of my cracking operations.

#### Acceptance Criteria

1. WHEN a user accesses the dashboard THEN the system SHALL display active agents count with total agents
2. WHEN the dashboard loads THEN it SHALL show running tasks count
3. WHEN displaying metrics THEN the system SHALL show recently cracked hashes count for the last 24 hours
4. WHEN showing resource usage THEN the system SHALL display a visual representation of hashrate over time
5. WHEN campaigns exist THEN the dashboard SHALL display a campaign overview list with progress indicators
6. WHEN no campaigns exist THEN the dashboard SHALL show an appropriate empty state message
7. WHEN displaying agent status THEN the system SHALL provide a detailed agent status panel
8. WHEN real-time updates are available THEN the dashboard SHALL automatically refresh data

### Requirement 3: Campaign Management Interface

**User Story:** As a security analyst, I want to manage campaigns through the NiceGUI interface, so that I can create, monitor, and control password cracking campaigns.

#### Acceptance Criteria

1. WHEN a user accesses the campaigns page THEN the system SHALL display a list of all campaigns with their status
2. WHEN viewing campaigns THEN the user SHALL be able to filter by campaign state (draft, active, archived)
3. WHEN searching campaigns THEN the system SHALL provide real-time search functionality by name and description
4. WHEN displaying campaigns THEN each campaign SHALL show name, status badge, progress bar, summary, and last updated time
5. WHEN a user clicks on a campaign THEN the system SHALL navigate to the campaign detail page
6. WHEN creating a new campaign THEN the system SHALL provide a campaign creation form
7. WHEN campaigns have attacks THEN the system SHALL display expandable attack details
8. WHEN managing campaigns THEN the user SHALL have options to edit and delete campaigns
9. WHEN campaigns span multiple pages THEN the system SHALL provide pagination controls

### Requirement 4: Agent Management Interface

**User Story:** As an operator, I want to monitor and manage agents through the NiceGUI interface, so that I can ensure optimal distribution of cracking tasks.

#### Acceptance Criteria

1. WHEN accessing the agents page THEN the system SHALL display all registered agents with their current status
2. WHEN viewing agent details THEN the system SHALL show agent name, status, last seen time, and capabilities
3. WHEN an agent is online THEN the system SHALL display it with an active status indicator
4. WHEN an agent is offline THEN the system SHALL show appropriate offline status
5. WHEN managing agents THEN the user SHALL be able to pause, resume, or remove agents
6. WHEN viewing agent performance THEN the system SHALL display hashrate and task completion metrics
7. WHEN agents report errors THEN the system SHALL display error information and status

### Requirement 5: Attack Configuration Interface

**User Story:** As a security analyst, I want to configure attacks through the NiceGUI interface, so that I can set up various password cracking strategies.

#### Acceptance Criteria

1. WHEN creating an attack THEN the system SHALL provide forms for different attack modes (dictionary, mask, hybrid)
2. WHEN configuring dictionary attacks THEN the user SHALL be able to select wordlists and rules
3. WHEN setting up mask attacks THEN the system SHALL provide mask pattern configuration
4. WHEN configuring attacks THEN the user SHALL be able to set attack priorities and parameters
5. WHEN attacks are created THEN they SHALL be associated with specific campaigns
6. WHEN viewing attacks THEN the system SHALL display attack progress and results
7. WHEN managing attacks THEN the user SHALL be able to pause, resume, or stop attacks

### Requirement 6: Resource Management Interface

**User Story:** As a user, I want to manage attack resources through the NiceGUI interface, so that I can upload and organize wordlists, rules, and other cracking resources.

#### Acceptance Criteria

1. WHEN accessing resources THEN the system SHALL display all available wordlists, rules, and mask files
2. WHEN uploading resources THEN the system SHALL provide file upload functionality with progress indicators
3. WHEN managing resources THEN the user SHALL be able to organize resources by categories
4. WHEN viewing resources THEN the system SHALL display file size, upload date, and usage statistics
5. WHEN downloading resources THEN the system SHALL provide secure download links
6. WHEN deleting resources THEN the system SHALL confirm the action and check for dependencies

### Requirement 7: User Management Interface

**User Story:** As an administrator, I want to manage users through the NiceGUI interface, so that I can control access and permissions within the system.

#### Acceptance Criteria

1. WHEN accessing user management THEN the system SHALL display all users with their roles and status
2. WHEN creating users THEN the system SHALL provide user creation forms with role assignment
3. WHEN managing users THEN administrators SHALL be able to modify user roles and permissions
4. WHEN viewing users THEN the system SHALL show user activity and last login information
5. WHEN deactivating users THEN the system SHALL provide user deactivation functionality
6. WHEN users have project associations THEN the system SHALL display and manage project memberships

### Requirement 8: Authentication and Authorization

**User Story:** As a user, I want secure authentication for the NiceGUI interface, so that my cracking operations and data remain protected.

#### Acceptance Criteria

1. WHEN accessing protected pages THEN the system SHALL require user authentication
2. WHEN logging in THEN the user SHALL use the same credentials as the existing web interface
3. WHEN authenticated THEN the system SHALL maintain session state across page navigation
4. WHEN unauthorized THEN the system SHALL redirect users to the login page
5. WHEN session expires THEN the system SHALL require re-authentication
6. WHEN accessing restricted features THEN the system SHALL enforce role-based permissions
7. WHEN logging out THEN the system SHALL clear session data and redirect to login

### Requirement 9: Real-time Updates and Notifications

**User Story:** As a user, I want real-time updates in the NiceGUI interface, so that I can monitor progress and respond to events as they occur.

#### Acceptance Criteria

1. WHEN campaigns are running THEN the interface SHALL update progress indicators in real-time
2. WHEN agents connect or disconnect THEN the system SHALL update agent status immediately
3. WHEN hashes are cracked THEN the system SHALL display notifications and update counters
4. WHEN errors occur THEN the system SHALL display appropriate error notifications
5. WHEN tasks complete THEN the system SHALL update task status and campaign progress
6. WHEN system events occur THEN the interface SHALL provide toast notifications or alerts

### Requirement 10: Responsive Design and Usability

**User Story:** As a user, I want a responsive and intuitive NiceGUI interface, so that I can effectively use the system on different devices and screen sizes.

#### Acceptance Criteria

1. WHEN accessing the interface on different screen sizes THEN the layout SHALL adapt appropriately
2. WHEN using the interface THEN navigation SHALL be intuitive and consistent
3. WHEN displaying data tables THEN they SHALL be sortable and filterable
4. WHEN forms are presented THEN they SHALL include proper validation and error messages
5. WHEN loading data THEN the system SHALL provide appropriate loading indicators
6. WHEN errors occur THEN the system SHALL display clear and actionable error messages
7. WHEN using the interface THEN it SHALL provide keyboard navigation support for accessibility
