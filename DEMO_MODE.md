# Demo Mode - IP Geolocation

## Overview
Demo mode allows the application to use simulated IP addresses instead of real client IPs for location tracking. This is useful for demonstrations, testing, and showcasing the fraud detection capabilities without requiring actual connections from different geographic locations.

## Configuration

### Enable Demo Mode
1. Navigate to Admin → Settings (`/admin/settings`)
2. Toggle "Enable Demo Mode" switch
3. Click "Save Settings"
4. Restart the application for changes to take effect

### Or Edit .env Manually
```env
DEMO_MODE=true   # Enable demo mode
DEMO_MODE=false  # Disable demo mode (use real IPs)
```

## Demo IP Addresses

When demo mode is enabled, the system rotates through these IPs:

| IP Address        | City      | Region                | Country        | Coordinates           |
|-------------------|-----------|----------------------|----------------|-----------------------|
| 195.154.122.113   | Paris     | Île-de-France        | France         | 48.8566°N, 2.3522°E   |
| 81.2.69.142       | London    | England              | United Kingdom | 51.5074°N, 0.1278°W   |
| 90.119.169.42     | Bordeaux  | Nouvelle-Aquitaine   | France         | 44.8378°N, 0.5792°W   |
| 87.98.154.146     | Lyon      | Auvergne-Rhône-Alpes | France         | 45.7640°N, 4.8357°E   |

## How It Works

### IP Rotation
- Each order or login action uses the next IP in the sequence
- The rotation is automatic and cycles through all 4 IPs
- Counter: `_demo_ip_counter` in `utils.py`

### Location Data
- Demo IPs return predefined location data (no API calls)
- Real geolocation API (ipapi.co) is bypassed for demo IPs
- Localhost IPs still return 'Local' location

### Fraud Detection
- Demo mode helps demonstrate fraud patterns:
  - Users ordering from different countries
  - Same IP used by multiple users
  - City mismatches between registered and detected locations

## Use Cases

### 1. Demonstrations
Show potential clients how the fraud detection system works without needing VPNs or proxy servers.

### 2. Testing
Test the graph analytics and location tracking features with diverse geographic data.

### 3. Development
Develop and debug location-based features without external dependencies or API rate limits.

### 4. Training
Train staff on how to interpret location data and identify suspicious patterns.

## Visual Indicators

When demo mode is active:
- **Blue banner** at the top of every page
- **Warning badges** on admin pages (Locations, Graph Analytics)
- **Status indicator** in Admin Settings page

## Production Mode

When `DEMO_MODE=false`:
- Uses real client IP addresses from `X-Forwarded-For` header or `request.remote_addr`
- Makes actual API calls to ipapi.co for geolocation
- No IP rotation or simulation

## Technical Details

### Files Modified
- `utils.py` - IP handling and demo data
- `config.py` - DEMO_MODE configuration
- `.env` - Demo mode flag
- `routes_web.py` - Context processor for templates
- `templates/base.html` - Demo mode banner
- `templates/admin_settings.html` - Settings UI

### Code Flow
```python
# 1. Check demo mode in config
if current_app.config.get('DEMO_MODE', False):
    # 2. Get next demo IP
    demo_data = DEMO_IPS[_demo_ip_counter % len(DEMO_IPS)]
    return demo_data['ip']
else:
    # 3. Get real IP
    return request.remote_addr

# 4. Get location data
for demo_data in DEMO_IPS:
    if demo_data['ip'] == ip_address:
        return demo_data  # Return demo location
        
# 5. Otherwise call ipapi.co
response = requests.get(f'https://ipapi.co/{ip_address}/json/')
```

## Best Practices

1. **Always disable in production** - Demo mode should only be used for testing and demonstrations
2. **Document when enabled** - Clearly communicate to users when viewing demo data
3. **Restart after changes** - Application restart required for config changes to take effect
4. **Monitor API usage** - Demo mode reduces ipapi.co API calls, useful for staying within free tier limits

## Troubleshooting

### Demo mode not working?
- Check `.env` file has `DEMO_MODE=true`
- Restart the Flask application
- Clear browser cache and session cookies

### IPs not rotating?
- Counter is global and persists during app lifetime
- Restart app to reset counter to 0

### Location data incorrect?
- Verify demo IP definitions in `utils.py`
- Check `DEMO_IPS` array for typos

## Future Enhancements

Potential improvements:
- Add more demo IPs from different continents
- Allow custom demo IP configuration via admin UI
- Add demo mode for different scenarios (fraud, normal, mixed)
- Export demo data for reporting and analysis
