# Database Expiration Remover

## Overview
This module prevents your Odoo database from expiring by automatically extending the trial period and maintaining database functionality. It provides multiple prevention methods and comprehensive monitoring.

## Features

### 🔧 Core Prevention Methods
- **Parameter Override**: Modifies system parameters to prevent expiration
- **Database Direct**: Direct database manipulation to override expiration
- **System Hook**: Overrides system methods to prevent expiration checks
- **Cron Override**: Continuous prevention through scheduled tasks

### 📊 Monitoring & Management
- **Real-time Status**: Monitor database expiration status
- **Automatic Extension**: Automatically extend trial periods
- **Manual Controls**: Manual expiration prevention when needed
- **Comprehensive Logging**: Detailed logs of all prevention activities

### 🛡️ Security & Access
- **System Admin Access**: Only system administrators can manage
- **Secure Operations**: All operations are logged and secured
- **Multiple Prevention Layers**: Redundant prevention methods

## Installation

1. **Copy the module** to your Odoo addons directory
2. **Update the app list** in Odoo
3. **Install the module** from the Apps menu
4. **Configure settings** in Administration > Database Expiration Remover

## Configuration

### Initial Setup
1. Go to **Administration > Database Expiration Remover**
2. Configure the **Database Expiration Core** settings
3. Set your preferred **prevention method**
4. Configure **prevention intervals**

### Prevention Methods

#### 1. Parameter Override (Recommended)
- Modifies system parameters
- Safe and reliable
- Easy to configure

#### 2. Database Direct
- Direct database manipulation
- More aggressive prevention
- Requires database access

#### 3. System Hook
- Overrides system methods
- Deep system integration
- Advanced prevention

#### 4. Cron Override
- Continuous prevention
- Scheduled maintenance
- Automated protection

## Usage

### Automatic Prevention
The module automatically prevents expiration through:
- **Hourly cron jobs** that check and extend trial periods
- **System parameter updates** that maintain active status
- **Database maintenance** that ensures proper functioning

### Manual Prevention
You can manually prevent expiration by:
1. Going to **Administration > Database Expiration Core**
2. Clicking **"Prevent Expiration Now"**
3. Monitoring the prevention status

### Manual Extension
You can manually extend the trial period by:
1. Going to **Administration > Database Expiration Remover**
2. Clicking **"Extend Trial"**
3. Setting the extension period

## Models

### 1. Database Expiration Remover
- **Purpose**: Main expiration management
- **Features**: Trial extension, expiration tracking
- **Access**: System administrators

### 2. Database Maintenance
- **Purpose**: Database health monitoring
- **Features**: Health checks, backup management
- **Access**: System administrators

### 3. Database Expiration Core
- **Purpose**: Core prevention system
- **Features**: Multiple prevention methods
- **Access**: System administrators

## Cron Jobs

### 1. Auto Extend Database Trial
- **Frequency**: Daily
- **Purpose**: Automatically extend trial periods
- **Model**: `database.expiration.remover`

### 2. Database Maintenance
- **Frequency**: Hourly
- **Purpose**: Database health monitoring
- **Model**: `database.maintenance`

### 3. Core Expiration Prevention
- **Frequency**: Hourly
- **Purpose**: Core prevention system
- **Model**: `database.expiration.core`

## System Parameters

The module sets and manages these system parameters:
- `database.expiration_date`: Database expiration date
- `database.trial_status`: Trial status (active/extended/permanent)
- `database.trial_start_date`: Trial start date
- `database.expiration_prevented`: Prevention status
- `database.last_prevention`: Last prevention timestamp

## Troubleshooting

### Common Issues

#### 1. Module Not Working
- **Check**: Module is properly installed
- **Verify**: Cron jobs are active
- **Ensure**: System administrator access

#### 2. Expiration Still Occurs
- **Check**: Prevention method is active
- **Verify**: Cron jobs are running
- **Ensure**: System parameters are set

#### 3. Database Errors
- **Check**: Database permissions
- **Verify**: System configuration
- **Ensure**: Proper module dependencies

### Debug Mode
Enable debug mode to see detailed logs:
1. Go to **Settings > Technical > Logging**
2. Set **Log Level** to **DEBUG**
3. Check logs for detailed information

## Security Considerations

### Access Control
- Only system administrators can access
- All operations are logged
- Secure parameter management

### Data Protection
- No sensitive data exposure
- Secure database operations
- Proper error handling

## Support

For support and questions:
1. Check the **Administration > Database Expiration Remover** interface
2. Review the **logs** for error messages
3. Verify **cron jobs** are running
4. Check **system parameters** are set correctly

## License

This module is licensed under LGPL-3.

## Version

- **Version**: 18.0.1.0.0
- **Odoo Version**: 18.0
- **Dependencies**: base

## Changelog

### Version 18.0.1.0.0
- Initial release
- Core prevention system
- Multiple prevention methods
- Comprehensive monitoring
- Automatic trial extension
- Database maintenance
- Security and access control

## Contributing

To contribute to this module:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Disclaimer

This module is provided as-is. Use at your own risk. The authors are not responsible for any issues that may arise from using this module.
