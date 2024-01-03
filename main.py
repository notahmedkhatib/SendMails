import os
import sys
import glob
import time
import shutil
import pathlib
import traceback
import subprocess
from typing import Union
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import utils

#--Raised when the specified table does not exist inside our database--#
class FilesNotFoundError(Exception):
    def __init__(self,msg):
        super().__init__(msg)

class InvalidMailClientError(Exception):
    def __init__(self,msg):
        super().__init__(msg)

class SendMails:
    """
    A flexible python package to send mails with attachments from your server.
    It supports mailx, mutt mail clients.
    Text attachments are split depending on the size limit (Should be lower than your Transfer protocol size limit).
    Non-textual attachments are compressed and attached.

    Parameters
    ----------
    `mail_client : str`
        The mail client you want to use. Supported: mailx, mutt. Default value is mailx.
    `footer : str`
        A custom message at the end of the mail.
    `debug_mode : bool`
        If True, will print the process for debugging. Default is False.
    `temp_dir : str`
        Path for a temporary directory where the split files would be stored. Default is current_dir/temp_dir.
    """

    def __init__(self, mail_client: str = "mailx", footer: str = "", debug_mode : bool = False, temp_dir : str = "temp_dir") -> None:

        #-Base Variables-#
        self.mail_files = []
        self.footer = footer
        self.split_size = 9000000
        self.debug_mode = debug_mode
        self.script_dir = os.getcwd()
        self.mail_client = mail_client
        self.temp_dir = os.path.join(os.getcwd(), temp_dir)

        #-Supported mail commands-#
        self.mail_commands = {
            "mailx": lambda subject, body, recipients : f'echo "{body}" | mailx -s "$(echo -e "{subject}\nContent-Type: text/html")" {recipients}',
            "mutt" : lambda subject, body, recipients : f'mutt -e "set content_type=text/html" -s "{subject}" -- {recipients}  <<EOF\n{body}\nEOF'
        }

        self.attachment_commands = {
            "mailx" : lambda filename, subject, filepath, recipients : f'echo "Attachment : {filename}" | mailx -s "{subject}" -a "{filepath}" {recipients}',
            "mutt" : lambda filename, subject, filepath, recipients : f'mutt -s "{subject}" -a "{filepath}" -- {recipients} <<EOF\nAttachment : {filename}\nEOF'
        }

        #-Throwing invalid mail client error if any invalid or unsupported client is passed-#
        if self.mail_client not in self.mail_commands:
            raise InvalidMailClientError(f"Invalid or Unsupported was passed : {self.mail_client}.")


    def base_setup(self):

        #-Storing the filepath in a list if provdied as a string-#
        if isinstance(self.given_files, str):
            self.given_files = [self.given_files] if any(self.given_files) else []

        #-Setting up the debugger-#
        self.debug = print if self.debug_mode else lambda x: None

        #-Creating the temp directory-#
        os.makedirs(self.temp_dir, exist_ok = True)

        #-Making all the paths absolute-#
        self.given_files = [os.path.abspath(file) for file in self.given_files]

        #-Storing invalid filepaths in a variable-#
        invalid_files = [f"- {file}" for file in self.given_files if not os.path.exists(file)]

        #-Printing the invalid files-#
        if invalid_files:
            invalid_files = '\n'.join(invalid_files)
            self.debug(f"\u274C Invalid Filepaths :\n{invalid_files}")

        #-Storing valid filepaths in a variable-#
        valid_files = [f"- {file}" for file in self.given_files if os.path.exists(file)]

        #-Printing the valid files-#
        valid_files = '\n'.join(valid_files)
        if valid_files:
            self.debug(f"\u2705 Valid Filepaths :\n{valid_files}")

        #-Storing only the valid paths in given_files-#
        self.given_files = [file for file in self.given_files if os.path.exists(file)]


    def files_setup(self):

        #-Changing the directory to the temp_folder-#
        os.chdir(self.temp_dir)

        #-Iterating the files-#
        for file_path in self.given_files:

            #-Checking for the file extensions-#
            path_data = pathlib.Path(file_path)
            file_name = path_data.stem
            file_ext = path_data.suffix

            #-Checking the file size-#
            if os.path.getsize(file_path) > self.split_size:

                #-Checking if it is a csv file-#
                if file_ext.lower() == '.csv':

                    #-Running the split csv function, which will split the csv into different parts-#
                    utils.split_csv(file_path, self.split_size)

                    #-Adding the result files to the main_files list-#
                    csv_files = glob.glob(os.path.join(os.getcwd(), f"{file_name}_*.csv"))
                    self.mail_files.extend(csv_files)

                #-Checking if it is an sql file-#
                elif file_ext.lower() == '.sql':

                    #-Running the split csv function, which will split the csv into different parts-#
                    utils.split_sql(file_path, self.split_size)

                    #-Adding the result files to the main_files list-#
                    sql_files = glob.glob(os.path.join(os.getcwd(), f"{file_name}_*.sql"))
                    self.mail_files.extend(sql_files)

                #-If not of the both supported types-#
                else:

                    #-Running the zip function to compress it-#
                    utils.zip_it(file_name, file_ext)

                    #-Checking if the zip exists and it got compressed to the desired size-#
                    if os.path.exists(f"{file_name}.zip") and os.path.getsize(f"{file_name}.zip") <= self.split_size:

                        #-Adding it to the main_files list-#
                        self.mail_files.append(f"{file_name}.zip")

            else:
                self.mail_files.append(file_path)


    def mail_setup(self):

        #-Adding trademark to the body and html breakline tags-#
        self.body = f"{self.body}\n\n{self.footer}".strip().replace("\n", "<br>")

        #-Creating the main mail_command-#
        self.mail_command = self.mail_commands[self.mail_client](self.subject, self.body, self.recipients)

        #-Sorting the mail files in ascending order-#
        self.mail_files.sort()


    def push_mail(self):

        #-Running the main mail first-#
        subprocess.call(self.mail_command, shell = True)

        #-Adding a sleep to maintain the order-#
        time.sleep(0.5)

        #-Iterating the files to attach-#
        for filepath in self.mail_files:

            #-Mail command for attached files-#
            filename = os.path.basename(filepath)
            command = self.attachment_commands[self.mail_client](filename, self.subject, filepath, self.recipients)
            subprocess.call(command, shell = True)

            #-Adding a sleep to maintain the order-#
            time.sleep(0.5)


    def cleanup(self):

        #-Changing the directory back to the script directory-#
        os.chdir(self.script_dir)

        #-Checking if the directory exists-#
        if os.path.exists(self.temp_dir):

            #-Deleting the directory with all its contents-#
            shutil.rmtree(self.temp_dir)


    def send(self, recipients: str, subject: str, body: str, files : Union[str, list] = ""):
        """
        Sends mail using linux mailx command. It takes recipients, subject, body parameters.
        It supports single and multiple attachments, as well as HTML elements.
        For SQLs, CSV files, it can be split and sent. For other files, it zips and attaches.

        Parameters
        ----------
        `recipients : str`
            List of receivers. For multiple, separate them using space.
        `subject : str`
            Subject for the mail.
        `body : str`
            Body of the mail. Can use html elements as well.
        `files : str | list`
            Can attach single or multiple files. Supports str for single and list for all. Default is empty str.
        """
        #-Base Variables-#
        self.body = body
        self.subject = subject
        self.given_files = files
        self.recipients = recipients

        try:

            #-Calling each process function-#
            self.base_setup()
            self.files_setup()
            self.mail_setup()
            self.push_mail()

        except:

            #-Printing the error out-#
            traceback.print_exc()

        finally:

            #-Running the cleanup module-#
            self.cleanup()