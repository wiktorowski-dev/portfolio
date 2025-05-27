create table exetra_accounts.users
(
    id              varchar(36)  not null primary key,
    email           varchar(256) unique not null
);

