# Cadeau
#### Video Demo:  https://www.youtube.com/watch?v=oXooZqjxA6I
#### Description: This website acts as a gift registry where users can both create wishlists as well as mark items on others' wishlists as purchased.

## Why the program exists

My family loves giving gifts, but sharing our wishlists with each other can be very cumbersome. We want to make sure that two people don't buy the same gift, but we don't want to be able to see who bought things on our own list. We typically make a google doc for our own wishlist which consists of items, prices, and urls. We then share the list with another family member and make them owner. It is then up to the new owner to take the creator off of the list and share with the rest of the family.

Cadeau is a website that automates this process by providing different wishlist views to different users based on their role. In addition, it allows a user to add to their own wishlist, even when it is already shared. They can also see what they asked for once the holiday has passed. Cadeau provides card-style layouts that standardize the way wishlists looks. Links, prices, and buy buttons are always in the same place, so confusion and mistakes are minimized.

## How the program works

Cadeau is built in a similar manor to problem set 9: Finance. It uses the Flask framework with python manipulating a SQL database on the back-end. The database holds several tables that relate item data to wishlist data to user data. Specific tables are used as bridges between datasets to ensure users are only shown what they have permission to see. Python code handles error-checking and redirects users to specific error pages based on what is wrong with the user input. Javascript was not heavily used in this project, but I plan on incorporating it into future improvements.

The front-end uses bootstrap as the primary CSS styling framework. Some styling has been overridden in styles.css as well as inline with the HTML. Jinja is heavily used to display different content depending on a user's permissions. Icons are custom for the most part, and all branding images were made specifically for Cadeau in Procreate.

## Possible improvements

As all applications this one can also be improved. Possible improvements:

- Incorporate a webscraper into the add_item page to auto-populate item data based on a provided URL
- Add images for each item that can be auto-populated from the URL or chosen by the user
- Add an ongoing wishlist that users can add to throughout the year, then pull from as they make event-specific wishlists
- Allow shared users to add a custom gift to someone's wishlist
- Create a dropdown of common events in the add_list menu that will auto-populate dates based on the next occurence of that event
- Add additional permission checks and security features so urls cannot be manipulated
- Allow user themes that change color schemes as well as choices for wishlist-specific themes
- Add user profile images that can auto-generate or be chosen by the user in order to more easily distinguish users on a shared list
- Incorporate javascript within HTML pages for form error checking
- Incorporate javascript bootstrap alerts for errors, successful actions, warnings, etc
- Further customize the UX and logos to give Cadeau a more unique feel
