import os
import wx
import pymysql
import sqlite3
import csv
import pickle

MY_BASE_PATH='path/to/my/sqlite_db.db'
MY_COMMAND_HISTORY_BASE_PATH='path/to/my/command_history_db.db'

def ConnectToDB(db_name):
    if db_name.count('sqlite_db'):
        db = MY_BASE_PATH
    elif db_name.count('history'):
        db = MY_COMMAND_HISTORY_BASE_PATH
    else:
        db = MY_COMMAND_HISTORY_BASE_PATH
    mode = "SQLite3"
    # Connect to the database
    if mode == "SQL":
        conn = pymysql.connect(host='host', user='user', password='pass', database='db_name')
        cursor = conn.cursor()
    else:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
    return cursor, conn, mode, db


class MainWindow(wx.Frame):
    def __init__(self, parent, title, mode, db):
        wx.Frame.__init__(self, parent, title=title, size=(600, 400))

        # Initialize the counter to 0
        self.counter = self.history_count()
        self.db=db
        self.results = []
        # Create the input and output controls
        self.input = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(-1, 80))
        self.input.SetFont(wx.Font(14, wx.MODERN, wx.NORMAL, wx.BOLD))
        self.output = wx.ListCtrl(self, style=wx.LC_REPORT | wx.SUNKEN_BORDER)

        self.output.InsertColumn(0, "colonne 1")
        self.output.InsertColumn(1, "colonne 2")
        self.output.InsertColumn(2, "colonne 3")

        # Create the submit, clear input, and clear output buttons
        self.submit = wx.Button(self, label="Submit")
        self.submit.Bind(wx.EVT_BUTTON, self.on_submit)
        self.clear_input = wx.Button(self, label="Clear Input")
        self.clear_input.Bind(wx.EVT_BUTTON, self.on_clear_input)
        self.clear_output = wx.Button(self, label="Clear Output")
        self.clear_output.Bind(wx.EVT_BUTTON, self.on_clear_output)
        self.save_as = wx.Button(self, label="Save as")
        self.save_as.Bind(wx.EVT_BUTTON, self.on_save_as)

        # Create a sizer for the buttons and the counter
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.submit, 0, wx.ALL, 10)
        button_sizer.Add(self.clear_input, 0, wx.ALL, 10)
        button_sizer.Add(self.clear_output, 0, wx.ALL, 10)
        button_sizer.Add(self.save_as, 0, wx.ALL, 10)
        button_sizer.AddStretchSpacer()


        self.counter_label = wx.StaticText(self, label="0 queries")
        self.counter_returned_label = wx.StaticText(self, label="0 result", size=(200, 40))
        self.counter_returned_label.SetFont(wx.Font(12, wx.MODERN, wx.NORMAL, wx.BOLD))

        counter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        counter_sizer.Add(self.counter_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)




        # Créer un panneau pour remplir l'espace restant
        filler_panel = wx.Panel(self)

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.Add(self.counter_returned_label, 0, wx.ALIGN_LEFT)
        bottom_sizer.AddStretchSpacer()

        # Ajouter le panneau de remplissage au sizer avec une proportion de 1
        bottom_sizer.Add(filler_panel, 1, wx.EXPAND)

        # Create a sizer to manage the layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(counter_sizer, 0, wx.EXPAND)
        sizer.Add(self.input, 0, wx.EXPAND)
        sizer.Add(button_sizer, 0, wx.CENTER)
        sizer.Add(self.output, 1, wx.EXPAND)

        sizer.Add(bottom_sizer, 0, wx.EXPAND)
        sizer.SetItemMinSize(filler_panel, 300, 40)

        # Set the sizer and center the window
        self.SetSizer(sizer)
        self.Center()

        # History
        self.history = []
        self.history_button = wx.Button(self, label="History")
        self.history_button.Bind(wx.EVT_BUTTON, self.load_history)

        # Create a horizontal sizer for the history button and the count label
        history_sizer = wx.BoxSizer(wx.HORIZONTAL)


        # Add the history button and count label to the sizer
        history_sizer.Add(self.history_button, 0, wx.ALL, 10)


        # Set the sizer for the history and count label
        sizer.Insert(0, history_sizer, 0, wx.EXPAND)

        self.counter_label.SetLabel(str(self.counter) + " queries")
        self.counter_returned_label.SetLabel("0 results")

    def on_save_as(self, event):
        if len(self.results)==0:
            return False
        else:
            # Create a file dialog to get the file path and extension
            wildcard = "CSV files (*.csv)|*.csv|SQLite3 files (*.db)|*.db|Python files (*.pkl)|*.pkl"
            dialog = wx.FileDialog(self, "Save results", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            if dialog.ShowModal() == wx.ID_OK:
                path = dialog.GetPath()
                extension = dialog.GetFilterIndex()

                # Process the chosen file extension
                if extension == 0:  # CSV
                    self.save_results_to_db(self.results, "csv", path)
                elif extension == 1:  # SQLite3
                    self.save_results_to_db(self.results, "sqlite", path)
                elif extension == 2:  # Python
                    self.save_results_to_db(self.results, "python", path)

            dialog.Destroy()

    def save_results_to_db(self, results, format, filepath):
        print(format, filepath, results[:5])
        conn = None
        try:
            # Connect to the database
            if format == 'csv':
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(results)
            elif format.count ("sqlite") or format.count("SQL"):
                # Save to database
                if format.count("sqlite"):
                    conn_to_save = sqlite3.connect(filepath)
                else:
                    conn_to_save = pymysql.connect(host='host', user='user', password='pass', database='db_name')
                cursor_to_save = conn_to_save.cursor()

                # Get column names from cursor description
                col_names = [descrip[0] for descrip in cursor.description]
                # Generate CREATE TABLE clause
                create_table_query = "CREATE TABLE IF NOT EXISTS "+self.table_name+" ("
                for col_name in col_names:
                    create_table_query += f"{col_name} text, "
                create_table_query = create_table_query[:-2] + ")"


                cursor_to_save.execute(create_table_query)

                # Generate INSERT INTO clause
                insert_into_query = f"INSERT INTO {self.table_name} VALUES ({', '.join(['?' for i in range(len(col_names))])})"


                cursor_to_save.executemany(insert_into_query, results)
                conn_to_save.commit()
                cursor_to_save.close()
                conn_to_save.close()

            elif format == 'python':
                with open(filepath, 'wb') as f:
                    pickle.dump(results, f)
            else:
                print('Invalid format')

        except Exception as e:
            print(e)
            wx.MessageBox("Failed to save results!", "Error", wx.OK | wx.ICON_ERROR)

        finally:
            if conn:
                conn.close()

    def save_results(self, results, format, filepath):
        if format == 'csv':
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(results)
        elif format == 'sqlite':
            conn = sqlite3.connect(filepath)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS results (col1 text, col2 text, col3 text)''')
            c.executemany('INSERT INTO results VALUES (?, ?, ?)', results)
            conn.commit()
            conn.close()
        elif format == 'python':
            with open(filepath, 'wb') as f:
                pickle.dump(results, f)
        else:
            print('Invalid format')



    def save_history(self):
        # Connect to the database
        conn = sqlite3.connect('history')
        c = conn.cursor()
        # Create the table if it does not exist
        c.execute('''CREATE TABLE IF NOT EXISTS history (query text)''')
        # Insert each query in the history into the table
        for query in self.history:
            c.execute('INSERT INTO history VALUES (?)', (query,))
        # Commit the changes and close the connection
        conn.commit()
        #conn.close()


    def save_current_query_in_history(self, current_query):
        try:
            # Connect to the database
            conn = sqlite3.connect(MY_COMMAND_HISTORY_BASE_PATH)
            c = conn.cursor()
            # Create the table if it does not exist
            c.execute('''CREATE TABLE IF NOT EXISTS history (query text)''')
            # Insert each query in the history into the table

            c.execute('INSERT INTO history VALUES (?)', (current_query,))
            # Commit the changes and close the connection
            conn.commit()
            conn.close()
        except Exception as e:
            print(e)


    def get_table_name(self, sql):
        conn_table=sqlite3.connect(self.db)
        cursor_table=conn_table.cursor()
        cursor_table.execute("SELECT name FROM sqlite_master WHERE type='table'")
        conn_table.commit()
        tables = cursor_table.fetchall()
        table_names = [table[0] for table in tables]
        conn_table.close()
        sql_words = sql.split(' ')
        for i, word in enumerate(sql_words):
            for table in table_names:
                if word.upper() == table.upper():
                    self.table_name = word
                    return self.table_name
        return table_names[-1]

    def on_submit(self, event):
        # Get the SQL from the input control
        sql = self.input.GetValue()
        # Initialize the result label to 0

        self.counter_returned_label.SetLabel("0 results")

        # Execute the SQL
        cursor.execute(sql)
        conn.commit()
        if len(sql)>0:
            # Increment the counter
            self.counter += 1
            self.counter_label.SetLabel(str(self.counter) + " queries")
            self.table_name = self.get_table_name(sql)
            print(self.table_name)

            self.save_current_query_in_history(sql)
        # Get the result
        result = cursor.fetchall()
        # Clear the output control
        self.output.ClearAll()
        self.counter_returned_label.SetLabel(str(len(result)) + " results")
        # Get the column names
        col_names = [descrip[0] for descrip in cursor.description]
        # Add the column names to the output control
        for i, col_name in enumerate(col_names):
            self.output.InsertColumn(i, col_name)
        for index, row in enumerate(result):
            self.output.InsertItem(index, str(row[0]))
            for j, value in enumerate(row[1:]):
                self.output.SetItem(index, j + 1, str(value))
            if index % 2 == 0:
                self.output.SetItemBackgroundColour(index, "LIGHTGREY")
            else:
                self.output.SetItemBackgroundColour(index, "WHITE")
            # Auto-size the columns
        for i in range(len(col_names)):
            self.output.SetColumnWidth(i, wx.LIST_AUTOSIZE)
            # Append the query to history
        self.history.append(sql)
        self.history = self.history[-200:]

        # Save the results
        self.results = [list(row) for row in result]



    def on_clear_input(self, event):
        '''
       Clear the Input text field
       :param event:
       :return:
       '''
        self.input.Clear()


    def on_clear_output(self, event):
        '''
        Clear the Output text field
        :param event:
        :return:
        '''
        self.output.ClearAll()
        self.results = []

    def history_count(self):
        '''
        Count the number of commands inhistory
        :return: the count
        '''
        cursor_hist, conn_hist, mode_hist, history_db = ConnectToDB('history')
        cursor_hist.execute('SELECT COUNT(*) FROM history')
        conn_hist.commit()
        result = cursor_hist.fetchone()[0]
        print(result)
        return result

    def load_history(self, event):
        '''
        Load the command's history
        :param event:
        :return:
        '''
        if not self.history:
            try:
                cursor_hist, conn_hist, mode_hist, history_db = ConnectToDB('history')
                cursor_hist.execute('SELECT * FROM history')
                conn_hist.commit()
                result = cursor_hist.fetchall()
                for index, row in enumerate(result):
                    if index<200:
                        entry=str(row[0])#.split("('")[1].split("',)")[0]
                        print(entry)
                        self.history.append(entry)
                conn_hist.close()
            except Exception as e:
                print(e)
                wx.MessageBox("No history found!", "Error", wx.OK | wx.ICON_ERROR)
                return
        dlg = wx.SingleChoiceDialog(self, "Select a query from history", "History", self.history)
        if dlg.ShowModal() == wx.ID_OK:
            query = dlg.GetStringSelection()
            self.input.SetValue(query)
        dlg.Destroy()


cursor, conn, mode, db = ConnectToDB('sqlite_db')
app = wx.App(False)
frame = MainWindow(None, "SQL Query", mode, db)
frame.Show()
app.MainLoop()

