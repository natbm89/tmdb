CREATE TABLE peliculas_generos (
    movie_id INT REFERENCES peliculas(movie_id),
    genero_id INT REFERENCES generos(genero_id),
    PRIMARY KEY (movie_id, genero_id)
);