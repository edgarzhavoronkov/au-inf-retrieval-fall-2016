# au-inf-retrieval-fall-2016

This is a simple CLI-based recommender engine for music. More details on wiki(in Russian)

## Running:
To run, clone this repository and execute `python recommender/recommender.py <db_path>`  
You will need data to operate on, you can download it from here: [link](https://drive.google.com/open?id=0B2baED5e1OEQSzhUWGh1Zk94QlE)  
`<db_path>` is a path to database
It launches in REPL mode, so you can type in following commands:
    
*  `signup <user_name>` - creates new user and signs you in
* `signin <user_name>` - logs you in as an existing user
* `like` - starts `like` dialog. Firstly asks you for an artist, then for a track
* `recommend` - recommends you ten songs, based on your likes. If you hadn't liked anything yet - you will be given ten the most popular songs. Similarly, if you aren't signed in, you will be given top ten songs.
* `tracks <artist_name>` - prints all tracks of given artist
* `liked` - prints all tracks you liked if you are signed in
* `exit` - to exit