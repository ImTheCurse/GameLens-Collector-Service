CREATE TABLE users(
	id serial primary key,
	username varchar(100)
);

CREATE TABLE choice(
	id serial primary key,
	choice_options JSON,
	selected varchar(100)
)

CREATE TABLE user_game(
	id serial primary key,
	user_id int,
	game_name varchar(100) not null,
	game_version varchar(100),

	CONSTRAINT user_game_id FOREIGN KEY (user_id)
    REFERENCES users(id)
);

CREATE TABLE run(
	id serial primary key,
	duration float not null,
	choice_id int,

	CONSTRAINT run_choice_id FOREIGN KEY (choice_id)
    REFERENCES choice(id)
)

