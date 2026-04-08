from datasets import load_dataset
from db import SessionLocal, Review

def seed_amazon_reviews(num_samples_per_class: int = 50):
    dataset = load_dataset(
        "SetFit/amazon_reviews_multi_en", 
        split="train", 
        streaming=True
    )

    db = SessionLocal()
    
    existing_reviews = set(r[0] for r in db.query(Review.review).all())

    positive_count = db.query(Review).filter(Review.label == 1).count()
    negative_count = db.query(Review).filter(Review.label == 0).count()
    
    new_reviews = []
    try:
        for row in dataset:
            if positive_count >= num_samples_per_class and negative_count >= num_samples_per_class:
                break

            rating = row['label'] 
            review_text = row['text']

            if not review_text or len(review_text) < 15 or review_text in existing_reviews:
                continue

            if rating >= 3 and positive_count < num_samples_per_class:
                label = 1
                positive_count += 1
            elif rating <= 1 and negative_count < num_samples_per_class:
                label = 0
                negative_count += 1
            else:
                continue
            
            new_review = Review(review=review_text, label=label)
            new_reviews.append(new_review)
            existing_reviews.add(review_text)
            

        if new_reviews:
            print(f"Inserting {len(new_reviews)} new items. This might take a few seconds...")
            db.add_all(new_reviews) 
            db.commit()
            print(f"New reviews inserted: {len(new_reviews)}")

    except Exception as e:
        print(e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_amazon_reviews(num_samples_per_class=2500)
