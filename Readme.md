# Simple Flask Login Restful API

## Quick Start

```text
docker-compose -p simplelogin  up
```

## Purpose

Design and implement two RESTful HTTP APIs for creating and verifying an account 
and password.

## Custom Setting

`secrect/dbpassword.txt` : set mysql db password

`secrect/salt.txt` : set password concat salt string before store into db

## Postman collection API Doucument 

Import `SimpleLoginRestful.postman_collection.json` into [Postman](https://www.postman.com/)

And click `Run collection` button and set `Delay` to 100ms. Press `Run` to test API.

## API introduce

### API_1 POST `/create_account`

#### Inputs:

A JSON payload containing the following fields:

```json
{
  "username": "<string>",
  "password": "<string>"
}
```

* "username": 

   a string representing the desired username for the account, with a 
minimum length of 3 characters and a maximum length of 32 characters.

* "password":

   a string representing the desired password for the account, with a 
minimum length of 8 characters and a maximum length of 32 characters, 
containing at least 1 uppercase letter, 1 lowercase letter, and 1 number.

  `The password will concat a salt string and use sha512 to store in db.`

#### Output:

Returns a JSON payload containing the following fields:
```json
{
  "success": <boolean>,
  "reson": "<string>"
}
```


* "success": 

   a boolean field indicating the outcome of the account creation process

* "reason": 
   
   a string field indicating the reason for a failed account creation process


### API_2 POST  `/verify`

#### Inputs:

A JSON payload containing the following fields:

**If the password verification fails five times, the user should wait one minute before 
attempting to verify the password again**


```json
{
  "username": "<string>",
  "password": "<string>"
}
```

* "username": 

   a string representing the username of the account being accessed.

* "password": 

    a string representing the password being used to access the account.

    `The password should concat a salt string and use sha512 to hash.`

    The salt is set in `secrect/salt.txt`.

    ```
    CryptoJS.enc.Hex.stringify(CryptoJS.SHA512( <password> + <salt> ))
    ```



#### Output:

Returns a JSON payload containing the following field:
```json
{
  "success": <boolean>,
  "reson": "<string>"
}
```
* "success": 
   
   a boolean field indicating the validity of the password provided for the given username

* "reason": 

  a string field indicating the reason