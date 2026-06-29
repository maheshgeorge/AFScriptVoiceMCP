"""
Kraft Heinz Recipe MCP Server
=============================
FastMCP server exposing 15 recipes across three Kraft Heinz brands:
  - Kraft Natural Cheese  (6 recipes)
  - Heinz AU              (5 recipes)
  - KraftHeinz.com        (4 recipes)

Transport : HTTP + SSE  (Render-compatible)
Auth      : Static Bearer token via KH_RECIPE_TOKEN env var
"""

import os
import json
from typing import Optional
from fastmcp import FastMCP

# ── Auth token (set in Render environment variables) ──────────────────────────
API_TOKEN = os.environ.get("KH_RECIPE_TOKEN", "kh-recipes-secret-token")

# ── Recipe data ───────────────────────────────────────────────────────────────
RECIPES = [
    # ── Kraft Natural Cheese ─────────────────────────────────────────────────
    {
        "id": "knc-001",
        "title": "Simply Lasagna",
        "slug": "simply-lasagna",
        "source_brand": "Kraft Natural Cheese",
        "meal_type": "Dinner",
        "prep_time": "20 min",
        "total_time": "1 hr 20 min",
        "servings": "8",
        "description": "A classic family lasagna made with Kraft Mozzarella and Parmesan cheeses, layered with ricotta and seasoned beef.",
        "ingredients": [
            "1½ lb lean ground beef",
            "1 jar (24 oz) pasta sauce",
            "1¾ cups water",
            "1 egg",
            "1 container (15 oz) ricotta",
            "2 tbsp dried parsley",
            "2 cups Kraft Shredded Mozzarella (divided)",
            "½ cup Kraft Grated Parmesan (divided)",
            "12 lasagna noodles (uncooked)",
        ],
        "steps": [
            "Heat oven to 350°F. Brown meat in large skillet on medium-high heat. Drain fat; stir in pasta sauce and water.",
            "Combine egg, ricotta, parsley, 1¼ cups mozzarella and ¼ cup Parmesan in bowl.",
            "Spread ½ cup meat sauce in 13×9 baking dish. Layer noodles, ricotta mixture, remaining meat sauce; repeat layers. Top with remaining cheeses.",
            "Cover tightly with foil. Bake 1 hour. Remove foil; rest 15 min before serving.",
        ],
        "tags": ["Pasta", "Comfort Food", "Bake", "Cheese", "Family Dinner"],
        "image_url": "https://www.kraftheinz.com/content/dam/kraft-natural-cheese/us/products/simply-lasagna-hero.jpg",
        "image_alt": "Golden baked lasagna in a white ceramic dish garnished with fresh basil",
        "source_url": "https://kraftnaturalcheese.com/recipe/simply-lasagna-recipe/",
    },
    {
        "id": "knc-002",
        "title": "Macaroni & Cheese",
        "slug": "macaroni-cheese-knc",
        "source_brand": "Kraft Natural Cheese",
        "meal_type": "Dinner",
        "prep_time": "10 min",
        "total_time": "30 min",
        "servings": "6",
        "description": "Rich, creamy homemade mac & cheese using Kraft Sharp Cheddar — a crowd-pleasing weeknight classic.",
        "ingredients": [
            "2 cups elbow macaroni",
            "¼ cup butter",
            "¼ cup all-purpose flour",
            "2 cups milk",
            "2 cups Kraft Shredded Sharp Cheddar",
            "Salt and black pepper to taste",
        ],
        "steps": [
            "Cook macaroni according to package directions; drain and set aside.",
            "Melt butter in saucepan over medium heat; whisk in flour. Gradually add milk, whisking until smooth. Cook until thickened, about 5 min.",
            "Stir in cheddar until fully melted. Season with salt and pepper.",
            "Combine sauce with macaroni and serve immediately.",
        ],
        "tags": ["Pasta", "Comfort Food", "Cheddar", "Quick", "Vegetarian"],
        "image_url": "https://www.kraftheinz.com/content/dam/kraft-natural-cheese/us/products/mac-cheese-hero.jpg",
        "image_alt": "Creamy macaroni and cheese in a bowl topped with shredded cheddar",
        "source_url": "https://kraftnaturalcheese.com/recipe/macaroni-cheese/",
    },
    {
        "id": "knc-003",
        "title": "Classic Cheeseburger",
        "slug": "classic-cheeseburger",
        "source_brand": "Kraft Natural Cheese",
        "meal_type": "Dinner",
        "prep_time": "10 min",
        "total_time": "20 min",
        "servings": "4",
        "description": "Juicy beef patties topped with melted Kraft Cheddar slices — the perfect backyard burger in under 20 minutes.",
        "ingredients": [
            "1½ lb 80/20 ground beef",
            "Salt and black pepper",
            "4 Kraft Natural Cheddar Slices",
            "4 burger buns",
            "Lettuce, tomato, onion, ketchup, mustard to serve",
        ],
        "steps": [
            "Divide beef into 4 equal patties; season both sides with salt and pepper.",
            "Grill or pan-fry over medium-high heat 4–5 min per side to desired doneness.",
            "Place one cheddar slice on each patty in the final minute of cooking; close lid to melt.",
            "Serve in buns with lettuce, tomato, onion and condiments.",
        ],
        "tags": ["Burger", "Grilling", "Cheddar", "Summer", "Quick"],
        "image_url": "https://www.kraftheinz.com/content/dam/kraft-natural-cheese/us/products/cheeseburger-hero.jpg",
        "image_alt": "Stacked classic cheeseburger with melted cheddar, lettuce and tomato",
        "source_url": "https://kraftnaturalcheese.com/recipe/classic-cheeseburger/",
    },
    {
        "id": "knc-004",
        "title": "Cheesy Stuffed Breadsticks",
        "slug": "cheesy-stuffed-breadsticks",
        "source_brand": "Kraft Natural Cheese",
        "meal_type": "Snack",
        "prep_time": "15 min",
        "total_time": "28 min",
        "servings": "8",
        "description": "Golden baked breadsticks stuffed with Kraft Mozzarella string cheese, brushed with garlic-parmesan butter and served with marinara.",
        "ingredients": [
            "1 can (11 oz) refrigerated breadstick dough",
            "8 Kraft Mozzarella String Cheese sticks",
            "3 tbsp butter, melted",
            "2 tbsp Kraft Grated Parmesan",
            "½ tsp garlic powder",
            "1 tsp dried parsley",
            "¾ cup marinara sauce",
            "2 tbsp plain yogurt",
        ],
        "steps": [
            "Heat oven to 375°F. Unroll dough and separate into 8 rectangles.",
            "Place 1 string cheese stick on centre of each rectangle; roll up, pressing seams and ends to seal. Place on baking sheet.",
            "Mix butter, Parmesan, garlic powder and parsley; brush generously over breadsticks.",
            "Bake 10–13 min until golden brown. Mix marinara with yogurt; serve alongside for dipping.",
        ],
        "tags": ["Snack", "Bake", "Mozzarella", "Appetizer", "Kid-Friendly"],
        "image_url": "https://www.kraftheinz.com/content/dam/kraft-natural-cheese/us/products/breadsticks-hero.jpg",
        "image_alt": "Golden stuffed breadsticks on a board with marinara dipping sauce",
        "source_url": "https://kraftnaturalcheese.com/recipe/cheesy-stuffed-breadsticks/",
    },
    {
        "id": "knc-005",
        "title": "Easy Spinach Artichoke Dip",
        "slug": "easy-spinach-artichoke-dip",
        "source_brand": "Kraft Natural Cheese",
        "meal_type": "Appetizer",
        "prep_time": "10 min",
        "total_time": "30 min",
        "servings": "16",
        "description": "Warm, gooey baked dip combining Kraft Parmesan, shredded Mozzarella, artichoke hearts and frozen spinach. Ready in 30 minutes.",
        "ingredients": [
            "1 pkg (10 oz) frozen chopped spinach, thawed and well-drained",
            "1 can (14 oz) artichoke hearts, drained and chopped",
            "1 cup Kraft Grated Parmesan",
            "½ cup Kraft Shredded Mozzarella",
            "½ cup mayonnaise",
            "½ tsp garlic powder",
        ],
        "steps": [
            "Heat oven to 350°F.",
            "Combine all ingredients in a bowl; mix until well blended.",
            "Spoon mixture into a 9-inch quiche dish or pie plate.",
            "Bake 20 min or until heated through. Serve warm with crackers or cut vegetables.",
        ],
        "tags": ["Dip", "Appetizer", "Parmesan", "Party", "Vegetarian"],
        "image_url": "https://www.kraftheinz.com/content/dam/kraft-natural-cheese/us/products/spinach-artichoke-dip-hero.jpg",
        "image_alt": "Bubbling spinach artichoke dip in a white baking dish with crackers",
        "source_url": "https://kraftnaturalcheese.com/recipe/easy-spinach-artichoke-dip-with-cheese/",
    },
    {
        "id": "knc-006",
        "title": "Hot Parmesan-Artichoke Dip",
        "slug": "hot-parmesan-artichoke-dip",
        "source_brand": "Kraft Natural Cheese",
        "meal_type": "Appetizer",
        "prep_time": "10 min",
        "total_time": "35 min",
        "servings": "24",
        "description": "A cheesy, crowd-pleasing baked dip with Kraft Parmesan, cream cheese, mayo and artichoke hearts. Make-ahead friendly.",
        "ingredients": [
            "1 pkg (8 oz) cream cheese, softened",
            "1 can (14 oz) artichoke hearts, drained and chopped",
            "¾ cup Kraft Grated Parmesan",
            "½ cup mayonnaise",
            "2 green onions, thinly sliced",
            "2 plum tomatoes, chopped",
        ],
        "steps": [
            "Heat oven to 350°F. Mix cream cheese, artichokes, Parmesan and mayo in bowl until combined.",
            "Spoon into shallow casserole dish sprayed with cooking spray.",
            "Bake 20–25 min until heated through and bubbly.",
            "Top with chopped tomatoes and green onions. Serve with crackers and vegetable dippers.",
        ],
        "tags": ["Dip", "Parmesan", "Party", "Bake", "Make-Ahead"],
        "image_url": "https://www.kraftheinz.com/content/dam/kraft-natural-cheese/us/products/parmesan-artichoke-dip-hero.jpg",
        "image_alt": "Hot parmesan artichoke dip garnished with tomatoes and green onions",
        "source_url": "https://kraftnaturalcheese.com/recipe/hot-parmesan-artichoke-dip/",
    },

    # ── Heinz AU ─────────────────────────────────────────────────────────────
    {
        "id": "hau-001",
        "title": "Baked Coconut Fish Curry",
        "slug": "baked-coconut-fish-curry",
        "source_brand": "Heinz AU",
        "meal_type": "Dinner",
        "prep_time": "20 min",
        "total_time": "1 hr 5 min",
        "servings": "4-6",
        "description": "A fragrant southern-Indian inspired curry with firm white fish baked in Heinz Big Red tomato soup and coconut milk, finished with a crispy tadka.",
        "ingredients": [
            "700–800g firm white fish, cut into 8cm pieces",
            "¼ cup tikka curry paste",
            "2 tbsp coconut or vegetable oil",
            "1 tbsp minced ginger",
            "1 can (420g) Heinz Big Red Condensed Tomato Soup",
            "400ml coconut milk",
            "1 tsp salt flakes",
            "2 sprigs fresh curry leaves",
            "1 tsp cumin seeds",
            "¼ cup coconut flakes",
            "Steamed rice and green beans to serve",
        ],
        "steps": [
            "Preheat oven to 200°C/180°C fan-forced. Marinate fish in 2 tbsp curry paste; set aside.",
            "Heat half the oil; sauté ginger and remaining curry paste 1 min. Stir in Heinz Big Red and coconut milk. Season; pour into 30×40cm baking dish.",
            "Pan-fry marinated fish 30 sec each side in hot pan; transfer to baking dish. Cover and bake 15 min.",
            "Heat remaining oil; fry curry leaves, cumin seeds and coconut flakes 1–2 min until fragrant. Spoon over fish. Serve on rice.",
        ],
        "tags": ["Seafood", "Curry", "Coconut", "Gluten-Free", "Heinz Big Red"],
        "image_url": "https://cdn.allotta.io/image/upload/f_auto/q_auto/v1776894345/Recipe_Asset_Images_Baked_Coconut_Fish_Curry_gfkljt.jpg",
        "image_alt": "Baked coconut fish curry in a ceramic dish topped with crispy curry leaves",
        "source_url": "https://www.heinz.com/en-AU/recipes/baked-coconut-fish-curry",
    },
    {
        "id": "hau-002",
        "title": "Chicken and Bean Burritos",
        "slug": "chicken-and-bean-burritos",
        "source_brand": "Heinz AU",
        "meal_type": "Lunch",
        "prep_time": "15 min",
        "total_time": "35 min",
        "servings": "8",
        "description": "Quick, family-friendly baked burritos packed with chicken thigh, Heinz Baked Beans, canned tomatoes and sweet chilli sauce.",
        "ingredients": [
            "1 tbsp oil",
            "1 onion, chopped",
            "1 garlic clove, finely chopped",
            "400g chicken thigh fillets, cut into strips",
            "2 × 300g cans Heinz Baked Beans in Tomato Sauce",
            "400g can chopped tomatoes",
            "2 tbsp sweet chilli sauce",
            "Salt and freshly ground pepper",
            "8 flour tortillas, warmed",
            "1 cup grated tasty cheese",
            "2 cups shredded iceberg lettuce",
            "1 cup chopped tomato",
            "8 tsp light sour cream",
            "Guacamole (optional)",
        ],
        "steps": [
            "Heat oil; sauté onion and garlic 2 min. Add chicken; cook 2–3 min until browned.",
            "Add Heinz Baked Beans, canned tomatoes and sweet chilli sauce; simmer 3 min. Season; remove from heat.",
            "Sprinkle cheese along centre of each tortilla; top with chicken mixture and roll to enclose. Arrange in ceramic baking dish. Spoon remaining filling across centre; sprinkle with remaining cheese.",
            "Bake at 180°C for 15–20 min until cheese is golden. Serve topped with lettuce, tomato, sour cream and guacamole.",
        ],
        "tags": ["Mexican", "Chicken", "Heinz Beanz", "Bake", "Family"],
        "image_url": "https://cdn.allotta.io/image/upload/v1718727706/dxp-images/brands/Recipes/global-recipes-heinz-au/chicken-and-bean-burritos/generated/chicken-and-bean-burritos-808408.jpg",
        "image_alt": "Baked chicken and bean burritos topped with melted cheese and sour cream",
        "source_url": "https://www.heinz.com/en-AU/recipes/chicken-and-bean-burritos",
    },
    {
        "id": "hau-003",
        "title": "Chilli Bean Tacos",
        "slug": "chilli-bean-tacos",
        "source_brand": "Heinz AU",
        "meal_type": "Dinner",
        "prep_time": "15 min",
        "total_time": "25 min",
        "servings": "6",
        "description": "Easy beef and Heinz Beanz Creationz tacos with fresh cucumber, tomato and grated cheese — great for a make-your-own family dinner.",
        "ingredients": [
            "1 tsp olive oil",
            "400g lean beef mince",
            "1 can (420g) Heinz Beanz Creationz Medium Salsa Chilli Beanz",
            "3 cups shredded lettuce",
            "1 medium cucumber, chopped",
            "2 medium tomatoes, finely chopped",
            "1 cup grated tasty cheese",
            "Taco shells",
        ],
        "steps": [
            "Heat oil in large non-stick pan; cook mince 5 min until well browned.",
            "Add Heinz Beanz Creationz; simmer 3 min. Season to taste.",
            "Spoon chilli bean filling into base of each taco shell.",
            "Top with chopped tomato, cucumber and shredded lettuce. Finish with grated cheese and serve immediately.",
        ],
        "tags": ["Mexican", "Beef", "Heinz Beanz", "Tacos", "Quick"],
        "image_url": "https://cdn.allotta.io/image/upload/v1718727693/dxp-images/brands/Recipes/global-recipes-heinz-au/chilli-bean-tacos/generated/chilli-bean-tacos-116001.jpg",
        "image_alt": "Chilli bean tacos filled with beef mince, lettuce, tomato and grated cheese",
        "source_url": "https://www.heinz.com/en-AU/recipes/chilli-bean-tacos",
    },
    {
        "id": "hau-004",
        "title": "Broccoli, Ricotta & Tomato Frittata",
        "slug": "broccoli-ricotta-tomato-frittata",
        "source_brand": "Heinz AU",
        "meal_type": "Breakfast",
        "prep_time": "15 min",
        "total_time": "1 hr",
        "servings": "6",
        "description": "A one-pan oven-baked frittata with roasted broccoli, ricotta, Heinz Big Red Condensed Tomato Soup and Parmesan. Make-ahead and meal-prep friendly.",
        "ingredients": [
            "1 tbsp extra virgin olive oil",
            "3 cups (250g) broccoli florets and stem, chopped",
            "1 garlic clove, crushed",
            "½ tsp chilli flakes (optional)",
            "Salt flakes and cracked pepper",
            "6 large free-range eggs",
            "3 spring onions, chopped",
            "½ can (210g) Heinz Big Red Condensed Tomato Soup",
            "200g fresh ricotta",
            "⅔ cup (100g) plain flour",
            "40g grated Parmesan, plus extra to serve",
            "Fresh basil, mint and rocket leaves to serve",
        ],
        "steps": [
            "Preheat oven to 180°C/160°C fan-forced. Toss broccoli, garlic and chilli in oil in a 1L baking dish. Season; roast 10 min. Cool slightly.",
            "Whisk eggs, spring onion, ½ cup Heinz Big Red, ricotta, flour and Parmesan. Season; pour over broccoli.",
            "Bake 30–35 min until egg is set through to centre. Cool slightly.",
            "Heat remaining Heinz Big Red; pour over frittata. Top with extra Parmesan and herbs. Serve with rocket dressed in lemon and olive oil.",
        ],
        "tags": ["Vegetarian", "Eggs", "Heinz Big Red", "Meal Prep", "Breakfast"],
        "image_url": "https://cdn.allotta.io/image/upload/f_auto/q_auto/v1776894346/Recipe_Asset_Images_Broccoli_Ricotta_Tomato_Frittata_ju7itf.jpg",
        "image_alt": "Broccoli ricotta frittata in a baking dish topped with tomato sauce and herbs",
        "source_url": "https://www.heinz.com/en-AU/recipes/broccoli-ricotta-tomato-frittata",
    },
    {
        "id": "hau-005",
        "title": "Cheesy Beef, Tomato & Bacon Pie",
        "slug": "cheesy-beef-tomato-bacon-pie",
        "source_brand": "Heinz AU",
        "meal_type": "Dinner",
        "prep_time": "20 min",
        "total_time": "55 min",
        "servings": "4",
        "description": "A rich, golden puff-pastry pie filled with beef mince, crispy bacon, grated cheddar and Heinz Big Red tomato soup. Freezer-friendly.",
        "ingredients": [
            "2 rashers bacon, diced",
            "1 tbsp olive oil",
            "500g beef mince",
            "1 brown onion, grated",
            "1 medium carrot, grated",
            "2 garlic cloves, crushed",
            "1 can (420g) Heinz Big Red Condensed Tomato Soup",
            "Salt flakes and cracked pepper",
            "1 sheet frozen puff pastry, partially thawed",
            "⅔ cup grated cheddar cheese",
            "1 egg, lightly beaten",
        ],
        "steps": [
            "Preheat oven to 200°C/180°C fan-forced. Cook bacon in frying pan on high until crisp; transfer to bowl. Brown mince in batches; transfer to bowl.",
            "Sauté onion, carrot and garlic until softened and golden. Return meat to pan with Heinz Big Red; cook until sauce has thickened. Season.",
            "Stir cheddar through filling; spoon into 24cm round pie tin. Cut pastry to fit; place on top and seal edges. Brush with egg wash.",
            "Bake 30–35 min until golden brown. Serve with root vegetable mash and steamed greens.",
        ],
        "tags": ["Pie", "Beef", "Bacon", "Heinz Big Red", "Puff Pastry", "Freezer-Friendly"],
        "image_url": "https://cdn.allotta.io/image/upload/f_auto/q_auto/v1776897087/Recipe_Asset_Images_Cheesy_Beef_Tomato_Bacon_Pie_tjh9ua.jpg",
        "image_alt": "Golden puff pastry beef and bacon pie with a flaky golden crust",
        "source_url": "https://www.heinz.com/en-AU/recipes/cheesy-beef-tomato-bacon-pie",
    },

    # ── KraftHeinz.com ───────────────────────────────────────────────────────
    {
        "id": "kh-001",
        "title": "Philadelphia 3-Step Cheesecake",
        "slug": "philadelphia-3-step-cheesecake",
        "source_brand": "KraftHeinz.com",
        "meal_type": "Dessert",
        "prep_time": "10 min",
        "total_time": "1 hr 20 min",
        "servings": "8",
        "description": "A creamy, indulgent baked cheesecake made with Philadelphia Brick Cream Cheese in just three simple steps.",
        "ingredients": [
            "2 pkgs (250g each) Philadelphia Brick Cream Cheese, softened",
            "½ cup sugar",
            "½ tsp vanilla",
            "2 eggs",
            "1 ready-to-use graham cracker crumb crust (9-inch)",
        ],
        "steps": [
            "Heat oven to 325°F.",
            "Beat cream cheese, sugar and vanilla with electric mixer until blended. Add eggs; beat just until combined.",
            "Pour into graham cracker crust.",
            "Bake 40 min or until centre is almost set. Cool to room temperature then refrigerate at least 3 hours before serving.",
        ],
        "tags": ["Dessert", "Cheesecake", "Philadelphia", "Bake", "Classic"],
        "image_url": "https://cdn.allotta.io/image/upload/f_auto/q_auto/v1714311951/Header_Image_tm3toz.png",
        "image_alt": "Creamy Philadelphia cheesecake on a plate with a graham cracker crust",
        "source_url": "https://www.kraftheinz.com/philadelphia/recipes/503503-philadelphia-3-step-cheesecake",
    },
    {
        "id": "kh-002",
        "title": "STOVE TOP One-Dish Chicken Bake",
        "slug": "stove-top-one-dish-chicken-bake",
        "source_brand": "KraftHeinz.com",
        "meal_type": "Dinner",
        "prep_time": "10 min",
        "total_time": "40 min",
        "servings": "6",
        "description": "A weeknight one-pan wonder: juicy chicken pieces baked under savory Stove Top Stuffing with a creamy mushroom soup sauce. Ready in 40 minutes.",
        "ingredients": [
            "1⅔ cups hot water",
            "1 pkg (6 oz) Stove Top Stuffing Mix for Chicken",
            "1½ lb boneless skinless chicken breasts, cut into bite-size pieces",
            "1 can (10¾ oz) condensed cream of mushroom soup",
            "⅓ cup sour cream",
        ],
        "steps": [
            "Heat oven to 400°F.",
            "Add hot water to Stove Top Stuffing Mix; stir just until moistened.",
            "Place chicken pieces in 13×9-inch baking dish. Mix mushroom soup and sour cream until blended; pour evenly over chicken. Top with moistened stuffing.",
            "Bake 30 min or until chicken is cooked through.",
        ],
        "tags": ["Chicken", "One-Pan", "Stove Top", "Comfort Food", "Weeknight"],
        "image_url": "https://cdn.allotta.io/image/upload/f_auto/q_auto/v1697471857/dxp-images/brands/Recipes/all-recipe-assets/stove-top-one-dish-chicken-bake/78599334e4ff48e0917c68081f85913c_uf7oc8.jpg",
        "image_alt": "One-dish chicken bake with golden stuffing topping in a casserole dish",
        "source_url": "https://www.kraftheinz.com/stove-top/recipes/501776-stove-top-one-dish-chicken-bake",
    },
    {
        "id": "kh-003",
        "title": "America's Favorite Grilled Cheese",
        "slug": "americas-favorite-grilled-cheese",
        "source_brand": "KraftHeinz.com",
        "meal_type": "Lunch",
        "prep_time": "5 min",
        "total_time": "10 min",
        "servings": "1",
        "description": "The ultimate classic: crispy buttery bread with two perfectly melted Kraft Singles American slices. Done in 10 minutes, loved by everyone.",
        "ingredients": [
            "2 slices white bread",
            "2 Kraft Singles American Slices",
            "2 tsp butter or margarine, softened",
        ],
        "steps": [
            "Place Kraft Singles between the two slices of bread.",
            "Spread softened butter on both outer faces of the sandwich.",
            "Cook in skillet over medium heat 3 min on each side, or until Singles are fully melted and both sides are golden brown.",
        ],
        "tags": ["Sandwich", "Quick", "Kraft Singles", "Lunch", "Kid-Friendly", "Classic"],
        "image_url": "https://cdn.allotta.io/image/upload/v1697473906/dxp-images/brands/Recipes/all-recipe-assets/americas-favorite-grilled-cheese-sandwich-recipe/generated/America-s-Favorite-Grilled-Cheese-Sandwich-Recipe-505975_rze56j.png",
        "image_alt": "Golden grilled cheese sandwich cut diagonally with melted Kraft Singles",
        "source_url": "https://www.kraftheinz.com/kraft-singles/recipes/505975-america-s-favorite-grilled-cheese-sandwich-recipe",
    },
    {
        "id": "kh-004",
        "title": "Fantasy Fudge",
        "slug": "fantasy-fudge",
        "source_brand": "KraftHeinz.com",
        "meal_type": "Dessert",
        "prep_time": "10 min",
        "total_time": "25 min",
        "servings": "24",
        "description": "A melt-in-your-mouth classic fudge made with Baker's Chocolate, Kraft Jet-Puffed Marshmallow Creme and walnuts — the ultimate holiday treat.",
        "ingredients": [
            "3 cups sugar",
            "¾ cup (1½ sticks) butter",
            "⅔ cup evaporated milk",
            "1 pkg (12 oz) Baker's Semi-Sweet Chocolate Chips",
            "1 jar (7 oz) Kraft Jet-Puffed Marshmallow Creme",
            "1 cup chopped walnuts",
            "1 tsp vanilla extract",
        ],
        "steps": [
            "Bring sugar, butter and evaporated milk to a full rolling boil in large heavy saucepan over medium heat, stirring constantly.",
            "Boil exactly 4 min while continuing to stir. Remove from heat.",
            "Immediately add chocolate chips; stir until completely melted. Stir in marshmallow creme, walnuts and vanilla until well blended.",
            "Pour into foil-lined 13×9-inch pan. Spread evenly; cool completely at room temperature. Cut into 1-inch squares.",
        ],
        "tags": ["Dessert", "Fudge", "Chocolate", "Holiday", "No-Bake", "Baker's"],
        "image_url": "https://www.kraftheinz.com/content/dam/kraft-heinz/us/products/fantasy-fudge-hero.jpg",
        "image_alt": "Rich chocolate fantasy fudge squares stacked on a white plate",
        "source_url": "https://www.kraftheinz.com/bakers/recipes/502173-fantasy-fudge",
    },
]

# ── Index helpers ─────────────────────────────────────────────────────────────
_by_id   = {r["id"]: r for r in RECIPES}
_by_slug = {r["slug"]: r for r in RECIPES}

# ── MCP server ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="Kraft Heinz Recipe Hub",
    instructions=(
        "You are a Kraft Heinz recipe assistant. You have access to 15 recipes "
        "across three brands: Kraft Natural Cheese, Heinz AU, and KraftHeinz.com. "
        "Use the available tools to search, filter and retrieve recipes, ingredients, "
        "steps and images."
    ),
)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_all_recipes() -> str:
    """Return a summary list of all 15 recipes with id, title, brand, meal type and image URL."""
    summary = [
        {
            "id":           r["id"],
            "title":        r["title"],
            "source_brand": r["source_brand"],
            "meal_type":    r["meal_type"],
            "total_time":   r["total_time"],
            "servings":     r["servings"],
            "image_url":    r["image_url"],
            "image_alt":    r["image_alt"],
            "slug":         r["slug"],
        }
        for r in RECIPES
    ]
    return json.dumps(summary, ensure_ascii=False, indent=2)


@mcp.tool()
def get_recipe_by_id(recipe_id: str) -> str:
    """
    Retrieve the full details of a recipe by its ID (e.g. 'knc-001', 'hau-002', 'kh-003').
    Returns all fields including ingredients, steps, image URL and source URL.
    """
    recipe = _by_id.get(recipe_id)
    if not recipe:
        return json.dumps({"error": f"No recipe found with id '{recipe_id}'"})
    return json.dumps(recipe, ensure_ascii=False, indent=2)


@mcp.tool()
def get_recipe_by_slug(slug: str) -> str:
    """
    Retrieve the full details of a recipe by its URL slug (e.g. 'simply-lasagna').
    Returns all fields including ingredients, steps, image URL and source URL.
    """
    recipe = _by_slug.get(slug)
    if not recipe:
        return json.dumps({"error": f"No recipe found with slug '{slug}'"})
    return json.dumps(recipe, ensure_ascii=False, indent=2)


@mcp.tool()
def search_recipes(
    query: Optional[str] = None,
    source_brand: Optional[str] = None,
    meal_type: Optional[str] = None,
    tag: Optional[str] = None,
) -> str:
    """
    Search recipes by keyword, brand, meal type or tag.

    Args:
        query:        Free-text search across title, description and tags.
        source_brand: Filter by brand — 'Kraft Natural Cheese', 'Heinz AU', or 'KraftHeinz.com'.
        meal_type:    Filter by meal type — 'Dinner', 'Lunch', 'Appetizer', 'Breakfast',
                      'Dessert', or 'Snack'.
        tag:          Filter by a single tag string (case-insensitive partial match).

    Returns a list of matching recipes with title, brand, meal type and image URL.
    """
    results = RECIPES

    if source_brand:
        results = [r for r in results if source_brand.lower() in r["source_brand"].lower()]

    if meal_type:
        results = [r for r in results if r["meal_type"].lower() == meal_type.lower()]

    if tag:
        results = [
            r for r in results
            if any(tag.lower() in t.lower() for t in r["tags"])
        ]

    if query:
        q = query.lower()
        results = [
            r for r in results
            if q in r["title"].lower()
            or q in r["description"].lower()
            or any(q in t.lower() for t in r["tags"])
            or any(q in i.lower() for i in r["ingredients"])
        ]

    if not results:
        return json.dumps({"message": "No recipes matched your search.", "count": 0})

    summary = [
        {
            "id":           r["id"],
            "title":        r["title"],
            "source_brand": r["source_brand"],
            "meal_type":    r["meal_type"],
            "total_time":   r["total_time"],
            "image_url":    r["image_url"],
            "image_alt":    r["image_alt"],
            "slug":         r["slug"],
        }
        for r in results
    ]
    return json.dumps({"count": len(summary), "recipes": summary}, ensure_ascii=False, indent=2)


@mcp.tool()
def get_recipe_ingredients(recipe_id: str) -> str:
    """
    Return just the ingredients list for a recipe by ID.
    Useful when a customer asks 'what do I need to make X?'
    """
    recipe = _by_id.get(recipe_id)
    if not recipe:
        return json.dumps({"error": f"No recipe found with id '{recipe_id}'"})
    return json.dumps({
        "recipe_id":   recipe["id"],
        "title":       recipe["title"],
        "servings":    recipe["servings"],
        "ingredients": recipe["ingredients"],
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_recipe_steps(recipe_id: str) -> str:
    """
    Return just the cooking steps for a recipe by ID.
    Useful when a customer is mid-cook and asks 'what's step 3?'
    """
    recipe = _by_id.get(recipe_id)
    if not recipe:
        return json.dumps({"error": f"No recipe found with id '{recipe_id}'"})
    return json.dumps({
        "recipe_id": recipe["id"],
        "title":     recipe["title"],
        "steps":     recipe["steps"],
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_recipe_image(recipe_id: str) -> str:
    """
    Return the image URL and alt text for a recipe by ID.
    Use this to display or share a recipe image.
    """
    recipe = _by_id.get(recipe_id)
    if not recipe:
        return json.dumps({"error": f"No recipe found with id '{recipe_id}'"})
    return json.dumps({
        "recipe_id": recipe["id"],
        "title":     recipe["title"],
        "image_url": recipe["image_url"],
        "image_alt": recipe["image_alt"],
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def list_brands() -> str:
    """Return the three source brands available in this recipe hub."""
    brands = sorted(set(r["source_brand"] for r in RECIPES))
    counts = {b: sum(1 for r in RECIPES if r["source_brand"] == b) for b in brands}
    return json.dumps({"brands": [{"name": b, "recipe_count": counts[b]} for b in brands]},
                      ensure_ascii=False, indent=2)


@mcp.tool()
def list_meal_types() -> str:
    """Return all available meal types and their recipe counts."""
    types = sorted(set(r["meal_type"] for r in RECIPES))
    counts = {t: sum(1 for r in RECIPES if r["meal_type"] == t) for t in types}
    return json.dumps({"meal_types": [{"name": t, "recipe_count": counts[t]} for t in types]},
                      ensure_ascii=False, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
