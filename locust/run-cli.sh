LOCUST="locust"
TARGET_HOST="http://fake-ai-service.stress-test.svc.cluster.local"
LOCUS_OPTS="-f /locust-test/test_case.py --headless --host=$TARGET_HOST"
LOCUST_MODE=${LOCUST_MODE:-standalone}

if [[ "$LOCUST_MODE" = "master" ]]; then
    MASTER_OPTS="--run-time 2m30s --csv /locust-test/result.csv"
    LOCUS_OPTS="$LOCUS_OPTS --master --master-port=5557 $MASTER_OPTS"

elif [[ "$LOCUST_MODE" = "worker" ]]; then
    WORKER_OPTS="-u 1000 -r 10"
    LOCUS_OPTS="$LOCUS_OPTS --worker --master-port=5557 --master-host=$LOCUST_MASTER_URL $WORKER_OPTS"
fi

echo "$LOCUST $LOCUS_OPTS"

$LOCUST $LOCUS_OPTS
