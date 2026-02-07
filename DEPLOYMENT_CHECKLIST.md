# Deployment Checklist - Admin Endpoint

## Pre-Deployment

- [ ] Read `IMPLEMENTATION_SUMMARY.md`
- [ ] Read `ADMIN_ENDPOINT_DEPLOYMENT.md`
- [ ] Review all modified files:
  - [ ] `app/config.py`
  - [ ] `app/exceptions.py`
  - [ ] `app/dependencies.py`
  - [ ] `app/schemas/match.py`
  - [ ] `app/services/match_service.py`
  - [ ] `app/routers/matches.py`
  - [ ] `.env` and `.env.example`

## Local Verification

- [ ] Python 3.8+ compatibility check
  ```bash
  python3 -m py_compile app/config.py app/exceptions.py app/dependencies.py
  python3 -m py_compile app/schemas/match.py app/services/match_service.py
  python3 -m py_compile app/routers/matches.py
  ```

- [ ] Run verification script
  ```bash
  python3 verify_implementation.py
  ```
  Expected: All components verified ✓

- [ ] Run configuration tests
  ```bash
  python3 test_admin_config.py
  ```
  Expected: All tests pass ✓

## Configuration

- [ ] Update `.env` with admin email(s)
  ```bash
  ADMIN_EMAILS_STR=andertvistholm@live.dk
  ```

- [ ] Verify admin user exists in database
  ```bash
  # Check if email can authenticate
  # Use existing magic link or request new one
  ```

- [ ] Double-check `.env` format
  - [ ] No trailing/leading spaces
  - [ ] Comma-separated for multiple admins
  - [ ] No quotes around email list

## Code Deployment

- [ ] Stage changes
  ```bash
  git add app/config.py app/exceptions.py app/dependencies.py
  git add app/schemas/match.py app/services/match_service.py app/routers/matches.py
  git add .env.example ADMIN_ENDPOINT_DEPLOYMENT.md IMPLEMENTATION_SUMMARY.md
  ```

- [ ] Review changes
  ```bash
  git diff --cached
  ```

- [ ] Create commit
  ```bash
  git commit -m "Add admin endpoint for updating match results with auto-scoring"
  ```

- [ ] Push to remote
  ```bash
  git push origin <branch-name>
  ```

- [ ] Verify in remote repository
  - [ ] Check commit on GitHub/GitLab
  - [ ] Review changed files
  - [ ] Confirm all files present

## Application Deployment

- [ ] Stop current application
  ```bash
  # If using systemd
  systemctl stop api-service

  # If using docker
  docker-compose down

  # If running locally, kill the process
  pkill -f uvicorn
  ```

- [ ] Pull latest code
  ```bash
  git pull origin <branch-name>
  ```

- [ ] Install/update dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Start application
  ```bash
  # If using systemd
  systemctl start api-service

  # If using docker
  docker-compose up -d

  # If running locally
  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &
  ```

- [ ] Wait for startup
  ```bash
  sleep 5
  ```

- [ ] Check application health
  ```bash
  curl http://localhost:8080/health
  ```
  Expected: `{"status": "ok"}` or similar

## Post-Deployment Verification

- [ ] Run verification script
  ```bash
  python3 verify_implementation.py
  ```
  Expected: ✓ All components verified

- [ ] Test endpoint availability
  ```bash
  # Check endpoint exists in OpenAPI docs
  curl http://localhost:8080/docs
  # Search for "PUT /matches/{match_id}/result"
  ```

- [ ] Test with admin user
  1. Authenticate as admin user
  2. Get a valid match ID
  3. Call: `PUT /matches/{match_id}/result`
  4. Send: `{"home_score": 1, "away_score": 0, "status": "completed"}`
  5. Verify: HTTP 200 response with updated match

- [ ] Test authorization
  1. Authenticate as non-admin user
  2. Attempt same endpoint
  3. Verify: HTTP 403 Forbidden response

- [ ] Check logs for errors
  ```bash
  # Check application logs
  tail -f /var/log/api.log
  # or for docker
  docker-compose logs -f api
  ```

- [ ] Verify database changes
  - [ ] Match record updated with new scores
  - [ ] Prediction records have points_earned calculated
  - [ ] No orphaned or partial records

## Monitoring (First 24 Hours)

- [ ] Monitor application errors
  - [ ] No 500 errors on admin endpoint
  - [ ] No timeout errors
  - [ ] No database connection issues

- [ ] Monitor admin actions
  - [ ] Log admin email for each update
  - [ ] Verify prediction calculations complete
  - [ ] Track prediction update counts

- [ ] Performance monitoring
  - [ ] Response times < 1 second
  - [ ] Database queries efficient
  - [ ] No memory leaks

- [ ] Alert on
  - [ ] Increased error rate
  - [ ] Slow response times
  - [ ] Database connectivity issues

## Rollback Plan (If Issues)

If critical issues occur:

- [ ] Stop application
  ```bash
  systemctl stop api-service  # or equivalent
  ```

- [ ] Revert code
  ```bash
  git revert <commit-hash>
  git push origin <branch-name>
  ```

- [ ] Pull reverted code
  ```bash
  git pull origin <branch-name>
  ```

- [ ] Restart application
  ```bash
  systemctl start api-service  # or equivalent
  ```

- [ ] Verify rollback
  ```bash
  python3 verify_implementation.py
  ```
  Expected: Admin endpoint should be unavailable

- [ ] Check if rollback needed for database
  - Predictions may have partial points_earned
  - May need manual cleanup depending on severity

## Post-Deployment Documentation

- [ ] Update team documentation
- [ ] Notify team of new endpoint availability
- [ ] Share deployment guide with ops team
- [ ] Document admin email list location
- [ ] Add to API documentation/README

## Long-term Maintenance

- [ ] Weekly: Review admin action logs
- [ ] Monthly: Check for performance degradation
- [ ] Quarterly: Review admin email list and revoke access as needed
- [ ] Quarterly: Check for security updates to dependencies
- [ ] As needed: Optimize prediction calculation if too slow

## Sign-off

- [ ] Deployment Engineer: _________________ Date: _______
- [ ] Code Reviewer: _________________ Date: _______
- [ ] QA Verification: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______

---

**Deployment Date**: _______
**Deployed By**: _______
**Environment**: [ ] Development [ ] Staging [ ] Production
**Notes**:

---

For support during deployment, refer to:
1. `IMPLEMENTATION_SUMMARY.md` - Overview
2. `ADMIN_ENDPOINT_DEPLOYMENT.md` - Detailed guide
3. `verify_implementation.py` - Automatic verification
