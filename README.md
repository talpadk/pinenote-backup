    usage: pinenote-backup.py [-h] [-b BLOCK_SIZE] -t {partitions,disk} [-d DESTINATION] [--skip-partition-table] [-u] [-n]
    
    A script for backing up a PineNote, may be useful for other devices using that can be accessed with rkdeveloptool
    
    options:
      -h, --help            show this help message and exit
      -b BLOCK_SIZE, --block_size BLOCK_SIZE
                            The max number of bytes to get at once, larger partitions/disks will be broken up into blocks according to this size to circumvent the 2GB limit, default is 1GB.
      -t {partitions,disk}, --type {partitions,disk}
                            The type of backup, partitions=attempt to get the individual partitions in separate files, disk=grap every byte including the partition table
      -d DESTINATION, --destination DESTINATION
                            The destination path to write the images to
      --skip-partition-table
                            Only for --type=partition, skip reading the bytes before the first partition
      -u, --skip-userdata-partition
                            Only for --type=partition, skip the partition named 'userdata', it is large and Android should be able to recreate it
      -n, --dry-run         Don't actually read bytes