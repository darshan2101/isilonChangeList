# Isilon Snapshot Management Tools

Python-based utilities for managing Dell EMC Isilon snapshots and changelists.

## Overview

This repository contains two main scripts for interacting with Dell EMC Isilon storage systems:
- `isilon_create_snap.py`: Creates snapshots of specified paths
- `isilon_generate_changelist.py`: Generates changelists between snapshots and outputs results in XML format

## Requirements

```txt
requests
urllib3
```

## Configuration

The scripts require Isilon configuration settings in either:
- Linux: `/etc/StorageDNA/DNAClientServices.conf`
- macOS: `/Library/Preferences/com.storagedna.DNAClientServices.plist`

Required configuration parameters:
- `IsilonClusterIP`: IP address of the Isilon cluster
- `IsilonClusterPort`: Port number for the Isilon API
- `IsilonUsername`: Username for authentication
- `IsilonPassword`: Password for authentication

## Usage

### Creating Snapshots

```bash
python isilon_create_snap.py -p PROJECT_NAME -s ISILON_SOURCE_PATH
```

Arguments:
- `-p, --projectname`: Name of the project
- `-s, --isilonsourcepath`: Source path to create snapshot from

### Generating Changelists

```bash
python isilon_generate_changelist.py -p PROJECT_NAME -g PROJECT_GUID -i SOURCE_INDEX --prevsnapshotid PREV_SNAPSHOT_ID --newsnapshotid NEW_SNAPSHOT_ID [-d]
```

Arguments:
- `-p, --projectname`: Project name
- `-g, --projectguid`: Project GUID
- `-i, --sourceindex`: Numeric index of source folders
- `--prevsnapshotid`: Previous snapshot ID
- `--newsnapshotid`: New snapshot ID
- `-d, --deletes`: Optional flag to include deleted files (mirror deletes)

## Output

The changelist generator creates XML files containing file changes between snapshots. The output includes:
- Added files
- Modified files
- Deleted files (if --deletes flag is used)
- File metadata (size, permissions, timestamps, ownership)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.