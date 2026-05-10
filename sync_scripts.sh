#!/usr/bin/env bash

#set -euo pipefail

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

find "${SCRIPTS_DEST}" -maxdepth 1 -type f -name '*.sh' -exec chmod +x {} +

if [[ "${SETUP_MODE}" == "kohya" ]]; then
  bash "${SCRIPTS_DEST}/setup_kohya.sh"
fi
