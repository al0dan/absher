#!/bin/bash
HOST="http://localhost:5000"
API_KEY="uqood-judge-access-key-2025"

echo "=== UQOOD ABSHER PRODUCTION VERIFICATION (FAST) ==="

# 1. Health Check
echo "[TEST] Health Check..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HOST/health)
if [ "$STATUS" -eq 200 ]; then echo "✅ Health (200 OK)"; else echo "❌ Health Failed ($STATUS)"; fi

# 2. Metrics Check
echo "[TEST] Metrics details..."
curl -s $HOST/metrics | grep "total_contracts" > /dev/null
if [ $? -eq 0 ]; then echo "✅ Metrics Endpoint Active"; else echo "❌ Metrics Endpoint Failed"; fi

# 3. Create Contract (Valid - ONCE)
echo "[TEST] Contract Creation (Valid)..."
RESPONSE=$(curl -s -X POST $HOST/api/contract \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"supplier":"TestSupplier","buyer":"TestBuyer","items":"Test Items Description","price":5000}')

if echo "$RESPONSE" | grep -q "id"; then
    echo "✅ Contract Created OK"
else
    echo "❌ Contract Creation Failed"
fi

# 4. Rate Limiting Test (Fast Spam with Invalid Data)
echo "[TEST] Rate Limiting (Spamming invalid requests)..."
LIMIT_HIT=0
for i in {1..15}; do
    # Sending INVALID data (short name) to avoid AI wait time, but trigger rate limiter count
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST $HOST/api/contract \
      -H "X-API-Key: $API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"supplier":"A","buyer":"B","items":"C","price":1}')
    
    if [ "$STATUS" -eq 429 ]; then
        LIMIT_HIT=1
        echo "✅ Rate Limit Hit on request $i (429 Too Many Requests)"
        break
    fi
done

if [ $LIMIT_HIT -eq 0 ]; then echo "❌ Rate Limiting Failed (Did not hit 429)"; fi

echo "=== VERIFICATION COMPLETE ==="
