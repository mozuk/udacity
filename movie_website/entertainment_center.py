from media import Movie
from fresh_tomatoes import open_movies_page


# function to generate html for all movies and open the browser with it
def generate_movies_html():
    # will contain all movies to be rendered to html selection
    all_movies = []

    asterix_movie = Movie(title="Asterix The Mansions of the Gods",
                          trailer_url="https://www.youtube.com/watch?v=WjiPfVza6X0",
                          poster_url="http://www.rotoscopers.com/wp-content/uploads/2014/02/asterix-movie-poster.jpg")
    all_movies.append(asterix_movie)

    dino_movie = Movie(title="Jurassic World",
                       trailer_url="https://www.youtube.com/watch?v=WuHj14V0xDk",
                       poster_url="http://www.bitacine.com/wp-content/uploads/2014/11/jurassic-world-trailer.jpg")
    all_movies.append(dino_movie)

    ant_man_movie = Movie(title="Ant-Man",
                          trailer_url="https://www.youtube.com/watch?v=QfOZWGLT1JM",
                          poster_url="http://www.impawards.com/2015/posters/ant_man_xlg.jpg")
    all_movies.append(ant_man_movie)

    # generate and open html file
    open_movies_page(all_movies)

if __name__ == '__main__':    
    generate_movies_html()