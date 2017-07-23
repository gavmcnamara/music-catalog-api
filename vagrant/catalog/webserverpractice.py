
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

# import CRUD Operations from Lesson 1
from tables import Base, Genre, Band
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create session and connect to DB
engine = create_engine('sqlite:///genresofmusic.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class webServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:

            if self.path.endswith("/delete"):
                genreIDPath = self.path.split("/")[2]
                myGenreQuery = session.query(Genre).filter_by(id= genreIDPath).one()
                if myGenreQuery !=[]:
                    self.send_response(200)
                    self.send_header('Content-type',    'text/html')
                    self.end_headers()
                    output = ""
                    output += "<html><body>"
                    output += "<h1>Are you sude you want to delete %s?" % myGenreQuery.name
                    output += """<form method='POST' enctype='multipart/form-data'
                        action='/genres/%s/delete' >""" % genreIDPath
                    output += "<input type= 'submit' value='Delete'>"
                    output += "</form>"
                    output += "</body></html>"
                    self.wfile.write(output)

            # Objective 3 Step 2 - Create /genres/new page
            if self.path.endswith("/genres/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h1>Make a New Genre</h1>"
                output += "<form method = 'POST' enctype='multipart/form-data' action = '/genres/new'>"
                output += "<input name = 'newGenreName' type = 'text' placeholder = 'New Genre Name' > "
                output += "<input type='submit' value='Create'>"
                output += "</form></html></body>"
                self.wfile.write(output)
                return
            if self.path.endswith("/edit"):
                genreIDPath = self.path.split("/")[2]
                myGenreQuery = session.query(Genre).filter_by(
                    id=genreIDPath).one()
                if myGenreQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = "<html><body>"
                    output += "<h1>"
                    output += myGenreQuery.name
                    output += "</h1>"
                    output += "<form method='POST' enctype='multipart/form-data' action = '/genres/%s/edit' >" % genreIDPath
                    output += "<input name = 'newGenreName' type='text' placeholder = '%s' >" % myGenreQuery.name
                    output += "<input type = 'submit' value = 'Rename'>"
                    output += "</form>"
                    output += "</body></html>"

                    self.wfile.write(output)

            if self.path.endswith("/genres"):
                genres = session.query(Genre).all()
                output = ""
                # Objective 3 Step 1 - Create a Link to create a new menu item
                output += "<a href = '/genres/new' > Make a New Genre Here </a></br></br>"

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output += "<html><body>"
                for genre in genres:
                    output += genre.name
                    output += "</br>"
                    # Objective 2 -- Add Edit and Delete Links
                    # Objective 4 -- Replace Edit href
                    output += "<a href ='/genres/%s/edit' >Edit </a> " % genre.id
                    output += "</br>"
                    output += "<a href =' /genres/%s/delete'> Delete </a>" % genre.id
                    output += "</br></br></br>"

                output += "</body></html>"
                self.wfile.write(output)
                return
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    # Objective 3 Step 3- Make POST method
    def do_POST(self):
        try:

            if self.path.endswith("/delete"):

                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                genreIDPath = self.path.split("/")[2]
                myGenreQuery = session.query(Genre).filter_by(id = genreIDPath).one()

            if myGenreQuery != []:
                session.delete(myGenreQuery)
                session.commit()
                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/genres')
                self.end_headers()

            if self.path.endswith("/edit"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newGenreName')
                    genreIDPath = self.path.split("/")[2]

                    myGenreQuery = session.query(Genre).filter_by(
                        id=genreIDPath).one()
                    if myGenreQuery != []:
                        myGenreQuery.name = messagecontent[0]
                        session.add(myGenreQuery)
                        session.commit()
                        self.send_response(301)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Location', '/genres')
                        self.end_headers()

            if self.path.endswith("/genres/new"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newGenreName')

                    # Create new Genre Object
                    newGenre= Genre(name=messagecontent[0])
                    session.add(newGenre)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/genres')
                    self.end_headers()

        except:
            pass


def main():
    try:
        server = HTTPServer(('', 8080), webServerHandler)
        print 'Web server running...open localhost:8080/genres in your browser'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()


if __name__ == '__main__':
    main()