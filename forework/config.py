import os
import yaml
import logging

REQUIRED_PYTHON_VERSION = (3, 4)
# If true, tasks are cached - all subsequent calls to `basetask.find_tasks` will
# use cached results, and will not discover newly added plugins unless restarted
ENABLE_TASKS_CACHE = True

src_dir = os.path.dirname(__file__)
tasks_dir = os.path.join(src_dir, 'tasks')
logfile = './forework.log'
loglevel_console = logging.WARNING
loglevel_file = logging.DEBUG


def yaml_join(loader, node):
    seq = loader.construct_sequence(node)
    if len(seq) < 1:
        return ''
    # strip leading slashes from everything except the first item
    components = [seq[0]]
    for item in seq[1:]:
        components.append(str(item).strip('/'))
    return os.path.join(*components)


yaml.add_constructor('!join', yaml_join)


class ForeworkConfig:
    '''
    Class to handle investigation configs, described in YAML.

    Example of YAML configuration:
    --- # Example investigation
    - investigation: Example investigation
      entrypoint: /path/to/image_or_directory_to_analyze
      tasks:
        PDFFile: [extract_pictures]
        TextFile: { grep: '^some pattern$' }
    '''

    def __init__(self, config_file):
        with open(config_file) as fd:
            config = yaml.load(fd)
        if len(config) == 0:
            raise Exception('No configuration found in {c!r}'.format(
                c=config_file
            ))
        if len(config) > 1:
            print('More than one configuration found, ignoring all except the '
                  'first')
        self._config = config[0]
        self._config_file = config_file

    def get(self, task_name):
        '''
        Return task-specific configuration as name -> value dictionary
        '''
        return self._config['tasks'].get(task_name, None)

    @property
    def investigation(self):
        '''
        Return the investigation name, or an empty string if no name is defined
        '''
        return self._config.get('investigation', '')

    @property
    def name(self):
        '''
        Return the investigation short name, or an empty string if no name is
        defined
        '''
        return self._config.get('name', '')

    @property
    def entrypoint(self):
        '''
        Return the investigation entry point, or an empty string if none is
        defined
        '''
        return self._config.get('entrypoint', '')
