TARGET_HOST=$(yq '.listen_host' config.yaml | tr -d '"')
NUM_USER=$(yq '.num_user' config.yaml | tr -d '"')
SPAWN_RATE=$(yq '.spawn_rate' config.yaml | tr -d '"')
DURATION=$(yq '.duration' config.yaml | tr -d '"')

LOCUST="locust"
LOCUS_OPTS="-f /locust-test/test_case.py --headless --host=$TARGET_HOST"
LOCUST_MODE=${LOCUST_MODE:-standalone}

if [[ "$LOCUST_MODE" = "master" ]]; then
    MASTER_OPTS="--run-time $DURATION --csv reports/result"
    LOCUS_OPTS="$LOCUS_OPTS --master --master-port=5557 $MASTER_OPTS"

elif [[ "$LOCUST_MODE" = "worker" ]]; then
    WORKER_OPTS="-u $NUM_USER -r $SPAWN_RATE"
    LOCUS_OPTS="$LOCUS_OPTS --worker --master-port=5557 --master-host=$LOCUST_MASTER_URL $WORKER_OPTS"
fi

mkdir -p reports

echo "$LOCUST $LOCUS_OPTS"

$LOCUST $LOCUS_OPTS
