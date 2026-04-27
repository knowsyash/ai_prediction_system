"""Quick Data Augmentation - Simple & Fast"""

import pandas as pd
import random
from pathlib import Path
from tqdm import tqdm

class SimpleAugmenter:
    """Simple text augmentation without external dependencies"""
    
    @staticmethod
    def synonym_simple(word):
        """Simple synonym replacement using basic word variations"""
        synonyms = {
            'good': ['great', 'nice', 'excellent', 'fine', 'wonderful'],
            'bad': ['poor', 'terrible', 'awful', 'disappointing'],
            'awesome': ['amazing', 'fantastic', 'incredible', 'superb', 'outstanding'],
            'camera': ['photography', 'picture quality', 'imaging', 'photo'],
            'battery': ['power', 'charge', 'battery life', 'backup'],
            'phone': ['device', 'handset', 'mobile', 'smartphone'],
            'beautiful': ['gorgeous', 'stunning', 'attractive', 'elegant'],
            'fast': ['quick', 'speedy', 'swift', 'rapid'],
            'love': ['enjoy', 'like', 'appreciate', 'adore'],
            'best': ['finest', 'top', 'greatest', 'superior'],
            'perfect': ['ideal', 'flawless', 'excellent', 'superb'],
            'display': ['screen', 'monitor', 'panel'],
            'quality': ['performance', 'standard', 'grade'],
            'price': ['cost', 'value', 'pricing'],
        }
        return random.choice(synonyms.get(word.lower(), [word]))
    
    def random_swap(self, text, n=2):
        """Randomly swap n words in the text"""
        words = text.split()
        if len(words) < 2:
            return text
        
        for _ in range(min(n, len(words) // 2)):
            if len(words) >= 2:
                idx1, idx2 = random.sample(range(len(words)), 2)
                words[idx1], words[idx2] = words[idx2], words[idx1]
        
        return ' '.join(words)
    
    def random_deletion(self, text, p=0.1):
        """Randomly delete words with probability p"""
        words = text.split()
        if len(words) == 1:
            return text
        
        new_words = [word for word in words if random.random() > p]
        
        if len(new_words) == 0:
            return random.choice(words)
        
        return ' '.join(new_words)
    
    def paraphrase_simple(self, text):
        """Simple paraphrasing using word substitution"""
        words = text.split()
        new_words = []
        
        for word in words:
            # 30% chance to replace common words
            if random.random() < 0.3 and len(word) > 3:
                new_words.append(self.synonym_simple(word))
            else:
                new_words.append(word)
        
        return ' '.join(new_words)
    
    def augment_review(self, title, review_text, rating, method='paraphrase'):
        """Augment a single review"""
        aug_title = str(title)
        aug_review = str(review_text)
        
        if method == 'paraphrase':
            aug_title = self.paraphrase_simple(aug_title)
            aug_review = self.paraphrase_simple(aug_review)
        elif method == 'swap':
            aug_title = self.random_swap(aug_title, n=1)
            aug_review = self.random_swap(aug_review, n=2)
        elif method == 'delete':
            aug_review = self.random_deletion(aug_review, p=0.1)
        
        return {
            'rating': rating,
            'title': aug_title,
            'review_text': aug_review
        }
    
    def augment_dataset(self, csv_path, output_path, multiplier=2):
        """Augment dataset by multiplier"""
        print(f"\nLoading: {csv_path}")
        df = pd.read_csv(csv_path)
        original_size = len(df)
        print(f"Original size: {original_size} reviews")
        
        augmented_data = df.to_dict('records')
        methods = ['paraphrase', 'swap']
        
        print(f"Generating {multiplier - 1} augmented version(s)...")
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Augmenting"):
            for i in range(multiplier - 1):
                method = methods[i % len(methods)]
                aug_review = self.augment_review(
                    row.get('title', ''),
                    row.get('review_text', ''),
                    row.get('rating', 5),
                    method=method
                )
                augmented_data.append(aug_review)
        
        aug_df = pd.DataFrame(augmented_data)
        aug_df = aug_df.drop_duplicates(subset=['review_text'], keep='first')
        aug_df.to_csv(output_path, index=False)
        
        final_size = len(aug_df)
        increase = final_size - original_size
        percentage = (increase / original_size) * 100
        
        print(f"\n✓ Success!")
        print(f"  Original: {original_size}")
        print(f"  Augmented: {final_size}")
        print(f"  Added: {increase} (+{percentage:.1f}%)")
        print(f"  Saved: {output_path}")


def main():
    base_dir = Path(__file__).parent
    output_dir = base_dir / 'augmented_data'
    output_dir.mkdir(exist_ok=True)
    
    augmenter = SimpleAugmenter()
    
    print("=" * 70)
    print("Quick Data Augmentation (No External Dependencies)")
    print("=" * 70)
    
    # Focus on iQOO Z10 as it has the least data
    products = [
        ('data_scrapping/iqoo_zx10/iqoo_z10_reviews.csv', 'iqoo_z10_augmented.csv', 3),  # 3x multiplier
        ('data_scrapping/iphone16/iphone16_reviews.csv', 'iphone16_augmented.csv', 2),   # 2x multiplier
        ('data_scrapping/iphone15/iphone15_reviews.csv', 'iphone15_augmented.csv', 2),   # 2x multiplier
    ]
    
    for csv_rel_path, output_name, multiplier in products:
        csv_path = base_dir / csv_rel_path
        output_path = output_dir / output_name
        
        if csv_path.exists():
            augmenter.augment_dataset(csv_path, output_path, multiplier=multiplier)
        else:
            print(f"\nSkipping - not found: {csv_path}")
    
    print("\n" + "=" * 70)
    print("All datasets augmented!")
    print(f"Output directory: {output_dir}")
    print("=" * 70)


if __name__ == '__main__':
    main()
