import sys


def extract_keys(path="auth_data.txt"):
    """
    The file must be in the same `src` working directory
    of the other python files, the following must be the format (each line with an information/credential):
        
        direct link of MLOL webpage (it depends to which library you're affiliated with)
        email address MLOL account
        password MLOL account
        email address PRESSREADER account
        password PRESSREADER account

    e.g.:
        $ cat auth_data.txt
        https://milano.medialibrary.it/home/index.aspx
        test@test.com
        testing!
        test2@test.com
        testing2!

       Parameters:
       path (str): path to authorization file

       Returns:
       str tuple, str tuple, str tuple:mlol link, mlol credentials, pressreader credentials
      """
    try:
        with open(path) as f:
            auth_data = f.read()

            auth_info = []

            for s in auth_data.splitlines():
                if not (s == ''):
                    auth_info.append(s)

            entrypoint_mlol = auth_info[0]
            mlol = auth_info[1], auth_info[2]
            pressreader = auth_info[3], auth_info[4]

            # Super chill sanitization
            if 'medialibrary.it' not in entrypoint_mlol or '@' not in pressreader[0]:
                sys.exit("Something is wrong with the data you've inserted, please check.")

            return entrypoint_mlol, mlol, pressreader

    except FileNotFoundError:
        open("/src/auth_data.txt", 'w')
        sys.exit("*** file doesn't exist, creating 'auth_data'"
                 " file, now fill it with data! ... exiting ***")
    except IndexError:
        sys.exit("error in reading auth_data, have you correctly inserted the login data?")