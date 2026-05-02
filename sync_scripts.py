#!/usr/bin/env bash
set -euo pipefail

READ_PROFILE="${READ_PROFILE:-vastreadall}"
WRITE_PROFILE="${WRITE_PROFILE:-vastoutput}"
SCRIPTS_DEST="${SCRIPTS_DEST:-/workspace/scripts}"
SETUP_MODE="${SETUP_MODE:-kohya}"

parse_args() {
  while (( $# > 0 )); do
    case "$1" in
      --wd)
        SETUP_MODE="wd"
        shift
        ;;
      --kohya)
        SETUP_MODE="kohya"
        shift
        ;;
      *)
        echo "Unknown argument: $1" >&2
        echo "Usage: $0 [--wd|--kohya]" >&2
        exit 2
        ;;
    esac
  done
}

parse_args "$@"

if ! command -v aws >/dev/null 2>&1; then
  tmpdir="$(mktemp -d)"
  oldpwd="$(pwd)"
  cd "${tmpdir}"
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip -q awscliv2.zip
  if command -v sudo >/dev/null 2>&1; then
    sudo ./aws/install --update
  else
    ./aws/install --bin-dir "${HOME}/.local/bin" --install-dir "${HOME}/.local/aws-cli" --update
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
  cd "${oldpwd}"
  rm -rf "${tmpdir}"
fi

if ! command -v aws >/dev/null 2>&1 && [[ -x "${HOME}/.local/bin/aws" ]]; then
  export PATH="${HOME}/.local/bin:${PATH}"
fi

mkdir -p "${HOME}/.aws"

cat > "${HOME}/.aws/credentials" <<EOF_CRED
[${READ_PROFILE}]
aws_access_key_id = ${S3_ACCESS_KEY_ID}
aws_secret_access_key = ${S3_SECRET_ACCESS_KEY}

[${WRITE_PROFILE}]
aws_access_key_id = ${S3_WRITE_KEY_ID}
aws_secret_access_key = ${S3_SECRET_WRITE_KEY}
EOF_CRED

  cat > "${HOME}/.aws/config" <<EOF_CFG
[profile ${READ_PROFILE}]
region = us-east-1
output = json

[profile ${WRITE_PROFILE}]
region = us-east-1
output = json
EOF_CFG

mkdir -p "${SCRIPTS_DEST}"
aws s3 sync "s3://${S3_BUCKET_NAME}/scripts/" "${SCRIPTS_DEST}/" \
  --endpoint-url "${S3_ENDPOINT_URL}" \
  --profile "${READ_PROFILE}"

chmod +x "${SCRIPTS_DEST}/setup_kohya.sh" "${SCRIPTS_DEST}/start_training.sh"
if [[ -f "${SCRIPTS_DEST}/train_wd_tagger.sh" ]]; then
  chmod +x "${SCRIPTS_DEST}/train_wd_tagger.sh"
fi
if [[ -f "${SCRIPTS_DEST}/prepare_wd_multilabel_dataset.py" ]]; then
  chmod +x "${SCRIPTS_DEST}/prepare_wd_multilabel_dataset.py"
fi

if [[ "${SETUP_MODE}" == "kohya" ]]; then
  bash "${SCRIPTS_DEST}/setup_kohya.sh"
fi

echo
echo "Done."
echo "Setup mode   : ${SETUP_MODE}"
echo "Read profile : ${READ_PROFILE}"
echo "Write profile: ${WRITE_PROFILE}"
echo "Read bucket  : ${S3_BUCKET_NAME}"
echo "Write bucket : ${S3_WRITE_BUCKET_NAME}"
echo "Scripts sync : s3://${S3_BUCKET_NAME}/scripts/ -> ${SCRIPTS_DEST}"
if [[ "${SETUP_MODE}" == "kohya" ]]; then
  echo "Stage 3      : bash ${SCRIPTS_DEST}/start_training.sh"
else
  echo "WD train     : bash ${SCRIPTS_DEST}/train_wd_tagger.sh"
fi
if [[ -f "${SCRIPTS_DEST}/train_wd_tagger.sh" ]]; then
  if [[ -f "${SCRIPTS_DEST}/prepare_wd_multilabel_dataset.py" ]]; then
    echo "WD prepare   : python3 ${SCRIPTS_DEST}/prepare_wd_multilabel_dataset.py --help"
  fi
fi
