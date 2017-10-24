drop table if exists birthdays;
create table birthdays (
  id integer primary key autoincrement,
  name text not null,
  birthdate integer not null,
  phone integer,
);
