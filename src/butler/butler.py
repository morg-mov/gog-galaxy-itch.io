from os.path import abspath
from os import getcwd
from exceptions import NotRunning, SecretMissing, AuthenticationError
from threading import Thread
from time import sleep, time
from socket import socket, gethostname, AF_INET, SOCK_STREAM
import logging, subprocess, json

class Butler(object):
    def __init__(self, butlerpath, dbpath, timeout=10):
        """
        Class for Butler Server and Client

        Parameters:
        - `butlerpath` (str): Path to butler client. Required.
        - `dbpath` (str): Path to butler database file. Required. Will be created automatically if not found.
        - `timeout` (int/float): Time to wait (in seconds) for the server secret before raising SecretMissing. Default: `10`.

        Vars:
        - `butlerpath` (str): Path to butler client. Required.
        - `dbpath` (str): Path to butler database file. Required. Will be created automatically if not found.
        - `isrunning` (bool): Butler daemon status. Will be set to `False` when `close()` is called or the daemon otherwise quits.
        - `stdout` (list): Butler daemon stdout lines.
        - `stderr` (list): Butler daemon stderr lines.
        - `process` (Popen): Butler daemon process class.
        - `threads` (dict): Dictionary list of threads for maintaining process info and output.
        - `server_secret` (str): Butler server secret key.
        - `server_address` (tuple): Daemon server address passed to TCP client.
        - `client_socket` (socket): TCP client socket for communicating with butler server.

        Functions:
        - `close()`: Close the butler daemon process.
        - `_check_process()`: Decorator function for checking if daemon is running. Raises NotRunning if not running.
        - `_read_stdout()`: Threaded process for checking stdout and outputting to logger and `stdout`.
        - `_read_stderr()`: Threaded process for checking stderr and outputting to logger and `stderr`.
        - `_run_check()`: Threaded process for checking the daemon process status.

        Exceptions:
        - `NotRunning`: Raised when trying to call a function on a closed butler daemon.
        - `SecretMissing`: Raised when the server secret key could not be found in stdout within timeout limit.
        - `AuthenticationError`: Raised when the client could not authenticate with the server. `server_secret` and the returned message from the auth request (`returned_msg`) is provided.

        """
        self.butlerpath = abspath(butlerpath)
        self.dbpath = abspath(dbpath)
        self.isrunning = False
        self.stdout = []
        self.stderr = []

        # Start the daemon process
        process_arglist = [self.butlerpath, 'daemon', '--json', '--dbpath', self.dbpath]
        self.process = subprocess.Popen(process_arglist, cwd=getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        self.isrunning = True

        # Threads for maintaining console output and process variables 
        self.threads = {
            "update_stdout": Thread(target=self._read_stdout),
            "update_stderr": Thread(target=self._read_stderr),
            "process_check": Thread(target=self._run_check),
        }
        for i in self.threads.values():
            i.start()

        # Wait for secret key to output to stdout. Stop after `timeout` seconds.
        timeout_finish = time() + timeout
        while time() < timeout_finish or self.server_secret is None: 
            for i in self.stdout:
                try:
                    i = json.loads(i)
                    self.server_secret = i['secret']
                    self.server_address = (i['tcp']['address'].split(":")[0], int(i['tcp']['address'].split(":")[1]))
                    break
                except (ValueError, KeyError):
                    continue

        # Check if server secret was found in stdout. Raise SecretMissing if not.
        if self.server_secret is None:
            raise SecretMissing('Client authentication secret could not be found in stdout. Did you point to the right executable?', self.stdout)
        
        # Create TCP connection to butler server and authenticate with found secret key.
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(self.server_address)
        auth_message = (json.dumps({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "Meta.Authenticate",
            "params": {
                "secret": self.server_secret
            }
        }) + '\n').encode('utf-8')
        self.client_socket.send(auth_message)

        auth_return = json.loads(self.client_socket.recv(1024))

        if not auth_return['result']['ok']:
            raise AuthenticationError('An error occurred while trying to authenticate the client connection with the server.', json.dumps(auth_return), self.server_secret)

    # Decorator function for checking if daemon is running, return None if not.
    def _check_process(func):
        def inner(self, *args, **kwargs):
            if not self.isrunning:
                raise NotRunning("The butler process is closed.")
            return func(self, *args, **kwargs)
        return inner

    def _read_stdout(self):
        while True:
            line = self.process.stdout.readline()
            if not line and self.process.poll() is not None: break
            if line:
                logging.debug(f'[butlerd] {line}')
                self.stdout.append(line.strip())

    def _read_stderr(self):
        while True:
            line = self.process.stderr.readline()
            if not line and self.process.poll() is not None: break
            if line:
                logging.error(f'[butlerd] {line}')
                self.stderr.append(line.strip())
    
    def _run_check(self):
        while True:
            if self.process.poll() is not None:
                self.isrunning = False
                break
            # Prevents accidental or purposeful tampering of isrunning.
            elif not self.isrunning:
                self.isrunning = True

    @_check_process
    def close(self):
        # Stop the butler process.
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
            for i in self.threads.values():
                i.join()


