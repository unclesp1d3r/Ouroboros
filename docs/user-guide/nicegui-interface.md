# NiceGUI Web Interface

## Overview

Ouroboros provides an alternative Python-native web interface built with [NiceGUI](https://nicegui.io/) that is integrated directly into the FastAPI backend application. This interface offers the same core functionality as the SvelteKit frontend but with a more integrated deployment option that eliminates the need for a separate frontend server.

The NiceGUI interface is particularly useful for:

- **Simplified Deployment**: Single application deployment without managing separate frontend and backend services
- **Python-Native Development**: Easier customization and extension by backend developers familiar with Python
- **Integrated Authentication**: Seamless integration with existing FastAPI authentication systems
- **Reduced Infrastructure**: Lower resource requirements for smaller deployments

## Key Features

### Core Functionality

The NiceGUI interface provides complete feature parity with the SvelteKit frontend:

- **Dashboard Interface**: System metrics, campaign overviews, and real-time monitoring
- **Campaign Management**: Create, monitor, and control password cracking campaigns
- **Agent Management**: Monitor and manage distributed cracking agents
- **Attack Configuration**: Set up various password cracking strategies (dictionary, mask, hybrid)
- **Resource Management**: Upload and organize wordlists, rules, and other cracking resources
- **User Management**: Control access and permissions (admin functionality)
- **Real-time Updates**: Live progress tracking and notifications via Server-Sent Events (SSE)

### Technical Benefits

- **Single Container Deployment**: Runs entirely within the FastAPI backend container
- **Shared Authentication**: Uses the same authentication system as existing APIs
- **Python Integration**: Direct access to backend services and database models
- **Responsive Design**: Mobile and tablet-friendly interface
- **Accessibility**: Keyboard navigation and screen reader support

## Accessing the Interface

The NiceGUI interface is available at the `/ui/` path when enabled:

```
http://localhost:8000/ui/
```

### URL Structure

- **Login**: `/ui/login` - Authentication page
- **Dashboard**: `/ui/dashboard` - Main system overview
- **Campaigns**: `/ui/campaigns` - Campaign management
- **Agents**: `/ui/agents` - Agent monitoring and control
- **Attacks**: `/ui/attacks` - Attack configuration
- **Resources**: `/ui/resources` - Resource management
- **Users**: `/ui/users` - User management (admin only)
- **Settings**: `/ui/settings` - System configuration

## Interface Components

### Dashboard

The dashboard provides a comprehensive overview of your Ouroboros deployment:

#### Metrics Cards

- **Active Agents**: Current online agents vs. total registered agents
- **Running Tasks**: Number of active cracking tasks
- **Cracked Hashes**: Recently cracked hashes (last 24 hours)
- **Resource Usage**: System load and performance indicators

#### Campaign Overview

- **Campaign List**: Accordion-style display of active campaigns
- **Progress Tracking**: Real-time progress bars with keyspace-weighted calculations
- **Status Indicators**: Color-coded campaign states (Running, Completed, Error, Paused)
- **Quick Actions**: Direct links to campaign details and management

#### Real-time Features

- **Live Updates**: Automatic refresh of metrics and progress indicators
- **Connection Status**: Visual indicators for SSE connection health
- **Toast Notifications**: Instant alerts for crack events and system status changes

### Campaign Management

Comprehensive campaign lifecycle management:

#### Campaign List View

- **Tabular Display**: Six-column layout showing Attack, Language, Length, Settings, Passwords to Check, and Complexity
- **Search and Filtering**: Real-time search by name and status-based filtering
- **Bulk Operations**: Multi-select with bulk actions (Check All, Bulk Delete)
- **Context Menus**: Per-campaign actions (Edit, Duplicate, Move Up/Down, Remove)

#### Campaign Creation

- **Guided Workflow**: Step-by-step campaign setup process
- **Hash List Integration**: Direct integration with uploaded hash lists
- **Attack Configuration**: Multiple attack types with parameter validation
- **Progress Estimation**: Real-time keyspace and complexity calculations

### Agent Management

Monitor and control your distributed cracking infrastructure:

#### Agent List View

- **Status Monitoring**: Real-time agent status with color-coded indicators (🟢 Online, 🟡 Idle, 🔴 Offline)
- **Performance Metrics**: Temperature, utilization, hashrate, and current job information
- **Hardware Details**: Agent name, operating system, and capability information

#### Agent Detail View

- **Tabbed Interface**: Organized into Settings, Hardware, Performance, and Log tabs
- **Settings Tab**: Agent label, enabled status, update intervals, project assignment
- **Hardware Tab**: Device enable/disable toggles, hardware acceleration settings
- **Performance Tab**: Line charts and utilization cards for performance monitoring
- **Log Tab**: Colored severity indicators for agent errors and events

### Attack Configuration

Set up sophisticated password cracking strategies:

#### Attack Mode Selection

- **Modal Dialogs**: Guided wizard steps for each attack type (not tabs)
- **Dictionary Attacks**: Wordlist selection, length ranges, modifier buttons
- **Mask Attacks**: Pattern configuration with custom charset support
- **Hybrid Attacks**: Combined dictionary and mask strategies
- **Real-time Estimation**: Live keyspace calculations via API integration

#### Resource Integration

- **File Browser**: Intuitive resource selection interface
- **Compatibility Checking**: Automatic validation of resource compatibility
- **Upload Integration**: Direct file upload with progress tracking

### Resource Management

Centralized management of cracking resources:

#### Resource Library

- **Categorized Display**: Organized by type (wordlists, rules, masks, charsets)
- **Metadata View**: File size, upload date, usage statistics
- **Search and Filter**: Quick resource discovery and organization

#### Upload Interface

- **Drag-and-Drop**: Modern file upload with progress indicators
- **Validation**: Automatic file type and format verification
- **Batch Operations**: Multiple file uploads with queue management

### User Management (Admin Only)

Administrative control over system access:

#### User Administration

- **User Listing**: Complete user roster with roles and status
- **Role Management**: Assign and modify user permissions
- **Activity Monitoring**: User login history and session information
- **Project Associations**: Manage user-project relationships

## Authentication and Security

### Session Management

The NiceGUI interface uses the same robust authentication system as the main Ouroboros APIs:

- **Session Cookies**: Secure HTTP-only cookies for session management
- **CSRF Protection**: Built-in protection against cross-site request forgery
- **Role-Based Access**: Granular permissions based on user roles
- **Session Expiration**: Automatic timeout with re-authentication requirements

### Security Features

- **HTTPS Enforcement**: All communications encrypted in production
- **Input Validation**: Comprehensive validation of all user inputs
- **Error Handling**: Secure error messages that don't leak sensitive information
- **Audit Logging**: Complete audit trail of user actions and system events

## Real-time Features

### Server-Sent Events (SSE)

The interface provides real-time updates through SSE connections:

#### Live Data Updates

- **Dashboard Metrics**: Automatic refresh of system statistics
- **Campaign Progress**: Real-time progress bar updates
- **Agent Status**: Instant agent connection/disconnection notifications
- **Crack Events**: Immediate notifications when hashes are cracked

#### Connection Management

- **Status Indicators**: Visual feedback on connection health
- **Automatic Reconnection**: Seamless recovery from connection drops
- **Manual Refresh**: "Refresh Now" button for manual data updates
- **Stale Data Warnings**: Indicators when data is more than 30 seconds old

### Notification System

Comprehensive notification system for user awareness:

#### Toast Notifications

- **Crack Events**: Instant alerts with rate limiting and batch grouping
- **System Status**: Connection status and error notifications
- **Action Feedback**: Success/error messages for user actions
- **Navigation Links**: Direct links to relevant views (hashlist, campaign)

## Responsive Design

### Mobile and Tablet Support

The interface is fully responsive and optimized for various screen sizes:

- **Adaptive Layouts**: Automatic layout adjustments for different screen sizes
- **Touch-Friendly**: Optimized touch targets and gestures
- **Horizontal Scrolling**: Data tables with horizontal scrolling on smaller screens
- **Collapsible Navigation**: Space-efficient navigation on mobile devices

### Accessibility Features

- **Keyboard Navigation**: Full keyboard accessibility for all interface elements
- **Screen Reader Support**: ARIA labels and semantic HTML structure
- **Focus Management**: Proper focus handling for interactive elements
- **High Contrast**: Support for high contrast and dark mode themes

## Configuration and Deployment

### Enabling the NiceGUI Interface

The NiceGUI interface is integrated into the main FastAPI application and can be enabled through configuration:

```python
# In app/main.py
from app.ui import setup_nicegui_interface

# Setup FastAPI app
app = FastAPI()

# Setup existing API routes
app.include_router(api_router, prefix="/api")

# Setup NiceGUI interface
setup_nicegui_interface(app)

# Run with NiceGUI integration
if __name__ == "__main__":
    ui.run_with(app, mount_path="/ui", storage_secret=settings.SECRET_KEY)
```

### Environment Variables

Configure the interface through standard Ouroboros environment variables:

```bash
# Enable NiceGUI interface
NICEGUI_ENABLED=true

# Storage secret for session management
SECRET_KEY=your-secret-key-here

# Database and other standard Ouroboros settings
DATABASE_URL=postgresql://user:pass@localhost/ouroboros
```

### Docker Deployment

The NiceGUI interface is included in the standard Ouroboros Docker deployment:

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - 8000:8000
    environment:
      - NICEGUI_ENABLED=true
      - SECRET_KEY=${SECRET_KEY}
    # ... other configuration
```

## Comparison with SvelteKit Frontend

### Feature Parity

Both interfaces provide identical functionality:

| Feature              | SvelteKit Frontend | NiceGUI Interface |
| -------------------- | ------------------ | ----------------- |
| Dashboard            | ✅                 | ✅                |
| Campaign Management  | ✅                 | ✅                |
| Agent Monitoring     | ✅                 | ✅                |
| Attack Configuration | ✅                 | ✅                |
| Resource Management  | ✅                 | ✅                |
| User Management      | ✅                 | ✅                |
| Real-time Updates    | ✅                 | ✅                |
| Responsive Design    | ✅                 | ✅                |
| Accessibility        | ✅                 | ✅                |

### Deployment Differences

| Aspect             | SvelteKit Frontend                | NiceGUI Interface          |
| ------------------ | --------------------------------- | -------------------------- |
| **Deployment**     | Separate frontend server          | Integrated with backend    |
| **Containers**     | 2 containers (frontend + backend) | 1 container (backend only) |
| **Build Process**  | Node.js build pipeline            | Python-only deployment     |
| **Resource Usage** | Higher (separate processes)       | Lower (single process)     |
| **Development**    | JavaScript/TypeScript             | Python-native              |
| **Customization**  | Frontend framework expertise      | Backend Python skills      |

### When to Choose Each Interface

#### Choose SvelteKit Frontend When

- You have dedicated frontend developers
- You need maximum performance and optimization
- You prefer modern JavaScript/TypeScript development
- You want to customize the UI extensively
- You're building a large-scale deployment

#### Choose NiceGUI Interface When

- You want simplified deployment and maintenance
- Your team is primarily Python-focused
- You need quick customization by backend developers
- You're running smaller or resource-constrained deployments
- You prefer integrated, single-container solutions

## Troubleshooting

### Common Issues

#### Interface Not Loading

- Verify `NICEGUI_ENABLED=true` in environment variables
- Check that the application is running with `ui.run_with()` integration
- Ensure the `/ui/` path is accessible (check for proxy configuration issues)

#### Authentication Problems

- Verify session cookies are being set correctly
- Check that the `SECRET_KEY` environment variable is configured
- Ensure HTTPS is enabled in production environments

#### Real-time Updates Not Working

- Check SSE connection status in browser developer tools
- Verify that the backend SSE endpoints are using `text/event-stream` media type
- Check for proxy or firewall issues blocking SSE connections

#### Performance Issues

- Monitor memory usage if handling large datasets
- Check for excessive SSE connections or update frequency
- Consider adjusting update intervals for better performance

### Debug Mode

Enable debug mode for additional logging and error information:

```python
# In development
ui.run_with(app, mount_path="/ui", storage_secret=settings.SECRET_KEY, debug=True)
```

### Log Analysis

Check application logs for NiceGUI-specific issues:

```bash
# Docker logs
docker compose logs app | grep -i nicegui

# Application logs
tail -f logs/app.log | grep -i "ui/"
```

## Future Enhancements

The NiceGUI interface is actively developed with planned enhancements:

- **Advanced Charting**: Enhanced performance visualization and analytics
- **Bulk Operations**: Extended bulk management capabilities
- **Custom Dashboards**: User-configurable dashboard layouts
- **Mobile App**: Progressive Web App (PWA) capabilities
- **Plugin System**: Extensible plugin architecture for custom functionality
- **Advanced Theming**: Additional theme options and customization

For the latest updates and feature requests, see the [Ouroboros GitHub repository](https://github.com/unclesp1d3r/Ouroboros).
