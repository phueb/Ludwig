from shutil import copyfile

from yourmodule import config


def preprocessing_job():
    print('Preprocessing + Saving data to file server...')


def your_job(param2val):
    print(param2val)
    print('Training neural network...')


def backup_job(param_name, job_name, allow_rewrite):
    """
    function is not imported from ludwigcluster because this would require dependency on worker.
    this informs LudwigCluster that training has completed (backup is only called after training completion)
    copies all data created during training to backup_dir.
    Uses custom copytree fxn to avoid permission errors when updating permissions with shutil.copytree.
    Copying permissions can be problematic on smb/cifs type backup drive.
    """
    src = config.Dirs.runs / param_name / job_name
    dst = config.Dirs.backup / param_name / job_name
    if not dst.parent.exists():
        dst.parent.mkdir(parents=True)
    copyfile(str(config.Dirs.runs / param_name / 'param2val.yaml'),
             str(config.Dirs.backup / param_name / 'param2val.yaml'))  # need to copy param2val.yaml

    def copytree(s, d):
        d.mkdir(exist_ok=allow_rewrite)  # set exist_ok=True if dst is partially missing files whcih exist in src
        for i in s.iterdir():
            s_i = s / i.name
            d_i = d / i.name
            if s_i.is_dir():
                copytree(s_i, d_i)
            else:
                copyfile(str(s_i), str(d_i))  # copyfile works because it doesn't update any permissions
    # copy
    print('Backing up data...  DO NOT INTERRUPT!')
    try:
        copytree(src, dst)
    except PermissionError:
        print('Backup failed. Permission denied.')
    except FileExistsError:
        print('Already backed up {}'.format(dst))
    else:
        print('Backed up data to {}'.format(dst))
