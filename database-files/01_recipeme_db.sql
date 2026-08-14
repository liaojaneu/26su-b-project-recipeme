CREATE DATABASE IF NOT EXISTS RecipeMe;

USE RecipeMe;


-- =====================================================
-- DROP EXISTING TABLES
-- =====================================================

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS recipe_tags;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS external_links;
DROP TABLE IF EXISTS follows;
DROP TABLE IF EXISTS collection_recipes;
DROP TABLE IF EXISTS collections;
DROP TABLE IF EXISTS review_replies;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS recipe_steps;
DROP TABLE IF EXISTS recipe_ingredients;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS users;


-- =====================================================
-- USERS
-- =====================================================

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL,
    account_status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- RECIPES
-- =====================================================

CREATE TABLE recipes (
    recipe_id INT AUTO_INCREMENT PRIMARY KEY,
    creator_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    prep_minutes INT,
    cook_minutes INT,
    difficulty VARCHAR(20),
    media_url VARCHAR(500),
    cooking_tips TEXT,
    substitutions TEXT,
    serving_suggestions TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    FOREIGN KEY (creator_id)
        REFERENCES users(user_id)
);


-- =====================================================
-- INGREDIENTS
-- =====================================================

CREATE TABLE ingredients (
    ingredient_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_name VARCHAR(100) NOT NULL UNIQUE
);


-- =====================================================
-- RECIPE INGREDIENTS
-- =====================================================

CREATE TABLE recipe_ingredients (
    recipe_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity DECIMAL(8,2),
    unit VARCHAR(30),

    PRIMARY KEY (recipe_id, ingredient_id),

    FOREIGN KEY (recipe_id)
        REFERENCES recipes(recipe_id)
        ON DELETE CASCADE,

    FOREIGN KEY (ingredient_id)
        REFERENCES ingredients(ingredient_id)
);


-- =====================================================
-- RECIPE STEPS
-- =====================================================

CREATE TABLE recipe_steps (
    step_id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL,
    step_number INT NOT NULL,
    instruction TEXT NOT NULL,

    FOREIGN KEY (recipe_id)
        REFERENCES recipes(recipe_id)
        ON DELETE CASCADE
);


-- =====================================================
-- REVIEWS
-- =====================================================

CREATE TABLE reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL,
    review_text TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    FOREIGN KEY (recipe_id)
        REFERENCES recipes(recipe_id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id),

    CHECK (rating BETWEEN 1 AND 5)
);


-- =====================================================
-- REVIEW REPLIES
-- =====================================================

CREATE TABLE review_replies (
    reply_id INT AUTO_INCREMENT PRIMARY KEY,
    review_id INT NOT NULL,
    user_id INT NOT NULL,
    reply_text TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (review_id)
        REFERENCES reviews(review_id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
);


-- =====================================================
-- COLLECTIONS
-- =====================================================

CREATE TABLE collections (
    collection_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    collection_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- =====================================================
-- COLLECTION RECIPES
-- =====================================================

CREATE TABLE collection_recipes (
    collection_id INT NOT NULL,
    recipe_id INT NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (collection_id, recipe_id),

    FOREIGN KEY (collection_id)
        REFERENCES collections(collection_id)
        ON DELETE CASCADE,

    FOREIGN KEY (recipe_id)
        REFERENCES recipes(recipe_id)
        ON DELETE CASCADE
);


-- =====================================================
-- FOLLOWS
-- =====================================================

CREATE TABLE follows (
    follower_id INT NOT NULL,
    creator_id INT NOT NULL,
    followed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (follower_id, creator_id),

    FOREIGN KEY (follower_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (creator_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CHECK (follower_id <> creator_id)
);


-- =====================================================
-- EXTERNAL LINKS
-- =====================================================

CREATE TABLE external_links (
    link_id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL,
    platform VARCHAR(40) NOT NULL,
    url VARCHAR(500) NOT NULL,

    FOREIGN KEY (recipe_id)
        REFERENCES recipes(recipe_id)
        ON DELETE CASCADE
);


-- =====================================================
-- TAGS
-- =====================================================

CREATE TABLE tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(75) NOT NULL,
    tag_type VARCHAR(30) NOT NULL
);


-- =====================================================
-- RECIPE TAGS
-- =====================================================

CREATE TABLE recipe_tags (
    recipe_id INT NOT NULL,
    tag_id INT NOT NULL,

    PRIMARY KEY (recipe_id, tag_id),

    FOREIGN KEY (recipe_id)
        REFERENCES recipes(recipe_id)
        ON DELETE CASCADE,

    FOREIGN KEY (tag_id)
        REFERENCES tags(tag_id)
        ON DELETE CASCADE
);


-- =====================================================
-- REPORTS
-- =====================================================

CREATE TABLE reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_user_id INT NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    target_id INT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',

    FOREIGN KEY (reporter_user_id)
        REFERENCES users(user_id)
);


-- =====================================================
-- AUDIT LOGS
-- =====================================================

CREATE TABLE audit_logs (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_user_id INT NOT NULL,
    action_type VARCHAR(60) NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    target_id INT NOT NULL,
    action_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (admin_user_id)
        REFERENCES users(user_id)
);


-- =====================================================
-- SAMPLE USERS
-- =====================================================

INSERT INTO users
    (full_name, email, role, account_status)
VALUES
    ('Rachel Green', 'rachel@example.com', 'home_cook', 'active'),
    ('Mark Smith', 'mark@example.com', 'chef', 'active'),
    ('Clark Johnson', 'clark@example.com', 'creator', 'active'),
    ('David Lopez', 'david@example.com', 'admin', 'active');


-- =====================================================
-- SAMPLE RECIPES
-- =====================================================

INSERT INTO recipes
    (creator_id, title, description, prep_minutes, cook_minutes,
     difficulty, media_url, cooking_tips, substitutions,
     serving_suggestions, is_active)
VALUES
    (2,
     'Garlic Chicken Pasta',
     'Creamy garlic chicken pasta.',
     15,
     25,
     'Easy',
     'https://example.com/chicken.jpg',
     'Do not overcook the chicken.',
     'Use half-and-half instead of cream.',
     'Serve with garlic bread.',
     TRUE),

    (3,
     'Crispy Chili Noodles',
     'Quick noodles with spicy chili sauce.',
     10,
     15,
     'Easy',
     'https://example.com/noodles.jpg',
     'Serve immediately.',
     'Use tofu instead of chicken.',
     'Top with green onions.',
     TRUE);


-- =====================================================
-- SAMPLE INGREDIENTS
-- =====================================================

INSERT INTO ingredients
    (ingredient_name)
VALUES
    ('Chicken Breast'),
    ('Garlic'),
    ('Noodles');


-- =====================================================
-- SAMPLE RECIPE INGREDIENTS
-- =====================================================

INSERT INTO recipe_ingredients
    (recipe_id, ingredient_id, quantity, unit)
VALUES
    (1, 1, 1.00, 'lb'),
    (1, 2, 3.00, 'cloves'),
    (2, 3, 8.00, 'oz');


-- =====================================================
-- SAMPLE RECIPE STEPS
-- =====================================================

INSERT INTO recipe_steps
    (recipe_id, step_number, instruction)
VALUES
    (1, 1, 'Cook the chicken until fully cooked.'),
    (1, 2, 'Add garlic and sauce to the pan.'),
    (2, 1, 'Cook noodles according to package directions.');


-- =====================================================
-- SAMPLE REVIEWS
-- =====================================================

INSERT INTO reviews
    (recipe_id, user_id, rating, review_text, status)
VALUES
    (1, 1, 5, 'Very easy and delicious.', 'active'),
    (2, 1, 4, 'Great flavor and quick to make.', 'active');


-- =====================================================
-- SAMPLE REVIEW REPLIES
-- =====================================================

INSERT INTO review_replies
    (review_id, user_id, reply_text)
VALUES
    (1, 2, 'Thanks for trying the recipe!'),
    (2, 3, 'Glad you enjoyed it!');


-- =====================================================
-- SAMPLE COLLECTIONS
-- =====================================================

INSERT INTO collections
    (user_id, collection_name, description)
VALUES
    (1, 'Weeknight Dinners', 'Quick meals for busy nights.'),
    (3, '30-Minute Dinners', 'Fast recipes for followers.');


-- =====================================================
-- SAMPLE COLLECTION RECIPES
-- =====================================================

INSERT INTO collection_recipes
    (collection_id, recipe_id)
VALUES
    (1, 1),
    (1, 2),
    (2, 2);


-- =====================================================
-- SAMPLE FOLLOWS
-- =====================================================

INSERT INTO follows
    (follower_id, creator_id)
VALUES
    (1, 2),
    (1, 3);


-- =====================================================
-- SAMPLE EXTERNAL LINKS
-- =====================================================

INSERT INTO external_links
    (recipe_id, platform, url)
VALUES
    (2, 'TikTok', 'https://tiktok.com/example'),
    (2, 'YouTube', 'https://youtube.com/example');


-- =====================================================
-- SAMPLE TAGS
-- =====================================================

INSERT INTO tags
    (tag_name, tag_type)
VALUES
    ('Italian', 'Cuisine'),
    ('Gluten-Free', 'Dietary'),
    ('Quick Meal', 'Category');


-- =====================================================
-- SAMPLE RECIPE TAGS
-- =====================================================

INSERT INTO recipe_tags
    (recipe_id, tag_id)
VALUES
    (1, 1),
    (1, 3),
    (2, 3);


-- =====================================================
-- SAMPLE REPORTS
-- =====================================================

INSERT INTO reports
    (reporter_user_id, target_type, target_id, reason, status)
VALUES
    (1, 'recipe', 2, 'Incorrect ingredient information.', 'open'),
    (2, 'review', 2, 'Inappropriate review content.', 'resolved');


-- =====================================================
-- SAMPLE AUDIT LOGS
-- =====================================================

INSERT INTO audit_logs
    (admin_user_id, action_type, target_type, target_id)
VALUES
    (4, 'Resolved Report', 'review', 2),
    (4, 'Archived Recipe', 'recipe', 2);
