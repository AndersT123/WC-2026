# Admin Endpoint Deployment Guide

## Overview

This document describes the admin endpoint for updating match results and automatically calculating prediction points in the World Cup Predictions API.

## Implementation Summary

The admin endpoint allows authorized administrators to update match results and trigger automatic point calculations for all predictions using the Witt Classic scoring system.

### Features

- ✅ Admin authorization via email whitelist
- ✅ Automatic prediction point calculation
- ✅ Full input validation (non-negative scores, valid status values)
- ✅ Comprehensive error handling
- ✅ Request/response logging
- ✅ Idempotent (can re-update completed matches)

## Changes Made

### 1. Configuration (app/config.py)

Added admin email configuration:
- `admin_emails_str: str = ""` - Comma-separated list of admin emails
- Property `admin_emails` - Parses string into list

### 2. Exception Handling (app/exceptions.py)

Added new exception:
- `ForbiddenError` (HTTP 403) - Raised when user lacks permission

### 3. Dependencies (app/dependencies.py)

Added new dependency:
- `get_admin_user()` - Verifies user email is in admin list

### 4. Schemas (app/schemas/match.py)

Added request schema:
- `UpdateMatchResultRequest` with:
  - `home_score: int` (must be ≥ 0)
  - `away_score: int` (must be ≥ 0)
  - `status: str` (one of: scheduled, in_progress, completed, cancelled)

### 5. Service Functions (app/services/match_service.py)

Added function:
- `update_match_result()` - Updates match scores, status, and timestamp

### 6. Router (app/routers/matches.py)

Added endpoint:
- `PUT /matches/{match_id}/result`
- Admin-only endpoint
- Automatically calculates prediction points
- Comprehensive logging

### 7. Environment Configuration (.env.example)

Added documentation:
- `ADMIN_EMAILS_STR` - Comma-separated admin emails

## Deployment Steps

### 1. Set Environment Variables

In your `.env` file:

```bash
# Admin Configuration
ADMIN_EMAILS_STR=admin@example.com,another-admin@example.com
```

For the hello-scaleway project:
```bash
ADMIN_EMAILS_STR=andertvistholm@live.dk
```

### 2. Deploy Code

```bash
git add .
git commit -m "Add admin endpoint for updating match results"
git push
```

### 3. Restart Application

Ensure the application is restarted to load the new configuration:

```bash
# If using systemd
systemctl restart api-service

# If using Docker
docker-compose restart api

# If running locally
# Kill the current process and restart uvicorn
```

### 4. Verify Deployment

Run the verification script:

```bash
python3 verify_implementation.py
```

Expected output: All components verified ✓

## API Endpoint

### Endpoint: `PUT /matches/{match_id}/result`

**Authentication:** Required (Cookie-based)
**Authorization:** Admin user (email in ADMIN_EMAILS_STR)

#### Request

```bash
curl -X PUT "http://localhost:8080/matches/123e4567-e89b-12d3-a456-426614174000/result" \
  -H "Content-Type: application/json" \
  -d '{
    "home_score": 2,
    "away_score": 1,
    "status": "completed"
  }'
```

#### Response (200 OK)

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "home_team": "France",
  "away_team": "Germany",
  "match_datetime": "2026-02-15T20:00:00",
  "venue": "Allianz Arena",
  "status": "completed",
  "home_score": 2,
  "away_score": 1,
  "created_at": "2026-01-31T12:00:00",
  "updated_at": "2026-01-31T21:40:00"
}
```

### Error Responses

**401 Unauthorized** - Not authenticated
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden** - Not an admin
```json
{
  "detail": "Admin access required"
}
```

**404 Not Found** - Match doesn't exist
```json
{
  "detail": "Match not found"
}
```

**422 Unprocessable Entity** - Invalid request data
```json
{
  "detail": [
    {
      "loc": ["body", "home_score"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

## Witt Classic Scoring Rules

When a match result is updated, prediction points are automatically calculated:

- **Exact Score (5 points)**: Predicted score matches actual score exactly
- **Correct Winner + 1 Right Score (3 points)**: Got the winner/draw right AND got one score exactly
- **Correct Winner/Draw (2 points)**: Got the winner/draw right but both scores wrong
- **One Right Score (1 point)**: Got one score right but wrong outcome
- **No Match (0 points)**: Everything else

## Logging

All admin actions are logged with the following information:

- Admin user email
- Match ID being updated
- Scores and status
- Number of predictions updated
- Any errors during prediction calculation

Example log entries:

```
INFO:app.routers.matches:Admin andertvistholm@live.dk updating match 123e4567...: 2-1, status=completed
INFO:app.routers.matches:Updated 47 predictions for match 123e4567...
INFO:app.routers.matches:Match 123e4567... result updated successfully
```

## Testing

### Run Configuration Tests

```bash
python3 test_admin_config.py
```

### Run Verification

```bash
python3 verify_implementation.py
```

### Run Integration Tests (pytest)

```bash
pytest tests/test_admin_endpoint.py -v
```

## Troubleshooting

### Issue: "Admin access required" (403)

**Cause**: User email is not in `ADMIN_EMAILS_STR`

**Solution**: Add the email to `.env`:
```bash
ADMIN_EMAILS_STR=existing@email.com,new-admin@email.com
```

Restart the application.

### Issue: "Match not found" (404)

**Cause**: Match ID doesn't exist or is malformed

**Solution**: Verify the match exists in the database and use correct UUID format

### Issue: "Invalid request data" (422)

**Cause**: Negative scores or invalid status

**Valid statuses**: `scheduled`, `in_progress`, `completed`, `cancelled`

**Valid scores**: Any non-negative integer (≥ 0)

## Security Considerations

1. **Email Whitelist**: Admins are identified by email from the JWT token
2. **No Public Write Access**: Only authenticated admins can call this endpoint
3. **Input Validation**: All scores and status values are validated
4. **Transaction Safety**: All changes are atomic (commit or rollback together)

## Monitoring

### Key Metrics to Track

1. **Admin Update Rate**: How often matches are being updated
2. **Prediction Calculation Time**: Performance of point calculations
3. **Error Rate**: Failures during prediction updates
4. **Admin Activity**: Which admins are making changes

### Recommended Alerts

- Alert if > 100 predictions updated per match (unusual)
- Alert if prediction calculation takes > 5 seconds
- Alert if admin updates more than 20 matches in 1 hour

## Support

For issues or questions:

1. Check the logs: `tail -f /var/log/api.log`
2. Verify configuration: `echo $ADMIN_EMAILS_STR`
3. Run verification: `python3 verify_implementation.py`
4. Check database: Verify match and prediction records exist

## Rollback Plan

If issues occur after deployment:

1. Revert the code:
```bash
git revert <commit-hash>
git push
```

2. Restart the application
3. Verify with: `python3 verify_implementation.py`

The endpoint removal is backward compatible - existing matches and predictions are unaffected.
