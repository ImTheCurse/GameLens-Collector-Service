CREATE TABLE users(
	id serial primary key,
	username varchar(100),
	user_password varchar(200) not null
);

CREATE TABLE choice(
	id serial primary key,
	run_id int,
	choice_options JSON not null,
	selected varchar(100) not null

	CONSTRAINT choice_run_id FOREIGN KEY (run_id)
	REFERENCES run(id)
)

CREATE TABLE user_game(
	id serial primary key,
	user_id int,
	game_name varchar(100) not null,
	game_version varchar(100) not null,
	version_date timestamp not null,

	CONSTRAINT user_game_id FOREIGN KEY (user_id)
    REFERENCES users(id)
);

CREATE TABLE run(
	id serial primary key,
	game_id int,
	duration float not null,

	CONSTRAINT run_game_id FOREIGN KEY (game_id)
	REFERENCES user_game(id)
)
