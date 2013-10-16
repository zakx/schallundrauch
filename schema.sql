drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  date date not null,
  time datetime not null,
  text text not null
);
