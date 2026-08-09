# Windows Code Signing

The endpoint is not currently code-signed. Commercial Windows distribution requires an Authenticode certificate, protected signing key, timestamping service, CI/release signing step and signature verification by the installer/updater. Private signing keys must never be committed to the repository.
