"""Breed lists for the add-pet dropdown, grouped by species."""

DOG_BREEDS = sorted([
    "Affenpinscher", "Afghan Hound", "Airedale Terrier", "Akita", "Alaskan Malamute", "American Bulldog",
    "Australian Cattle Dog", "Australian Shepherd", "Basenji", "Basset Hound", "Beagle", "Bernese Mountain Dog",
    "Bichon Frise", "Bloodhound", "Border Collie", "Boston Terrier", "Boxer", "Brittany", "Bulldog",
    "Bullmastiff", "Cairn Terrier", "Cavalier King Charles Spaniel", "Chihuahua", "Chow Chow", "Cocker Spaniel",
    "Collie", "Corgi (Pembroke Welsh)", "Dachshund", "Dalmatian", "Doberman Pinscher", "English Springer Spaniel",
    "French Bulldog", "German Shepherd", "German Shorthaired Pointer", "Golden Retriever", "Great Dane",
    "Great Pyrenees", "Greyhound", "Havanese", "Husky (Siberian)", "Irish Setter", "Jack Russell Terrier",
    "Labradoodle", "Labrador Retriever", "Lhasa Apso", "Maltese", "Mastiff", "Miniature Schnauzer", "Newfoundland",
    "Papillon", "Pit Bull", "Pomeranian", "Poodle", "Pug", "Rhodesian Ridgeback", "Rottweiler", "Saint Bernard",
    "Samoyed", "Shar Pei", "Shetland Sheepdog", "Shiba Inu", "Shih Tzu", "Vizsla", "Weimaraner",
    "West Highland White Terrier", "Whippet", "Yorkshire Terrier",
])

CAT_BREEDS = sorted([
    "Abyssinian", "American Shorthair", "Balinese", "Bengal", "Birman", "Bombay", "British Shorthair",
    "Burmese", "Chartreux", "Cornish Rex", "Devon Rex", "Egyptian Mau", "Exotic Shorthair", "Himalayan",
    "Maine Coon", "Manx", "Norwegian Forest Cat", "Ocicat", "Oriental Shorthair", "Persian", "Ragdoll",
    "Russian Blue", "Savannah", "Scottish Fold", "Siamese", "Siberian", "Singapura", "Somali", "Sphynx",
    "Tonkinese", "Turkish Angora", "Turkish Van",
])

RABBIT_BREEDS = sorted([
    "American Fuzzy Lop", "Californian", "Dutch", "English Angora", "English Lop", "Flemish Giant", "Harlequin",
    "Himalayan", "Holland Lop", "Lionhead", "Mini Lop", "Mini Rex", "Netherland Dwarf", "New Zealand", "Rex",
])

BIRD_BREEDS = sorted([
    "African Grey Parrot", "Amazon Parrot", "Budgerigar (Parakeet)", "Canary", "Cockatiel", "Cockatoo",
    "Conure", "Dove", "Finch", "Lovebird", "Macaw", "Parrotlet", "Quaker Parrot",
])

HAMSTER_BREEDS = sorted([
    "Chinese Hamster", "Dwarf Campbell's Russian", "Dwarf Winter White", "Roborovski Dwarf", "Syrian (Golden)",
])

GUINEA_PIG_BREEDS = sorted([
    "Abyssinian", "American", "Coronet", "Peruvian", "Silkie (Sheltie)", "Skinny Pig (Hairless)", "Teddy",
    "Texel",
])

TURTLE_BREEDS = sorted([
    "Box Turtle", "Common Musk Turtle", "Painted Turtle", "Red-Eared Slider", "Russian Tortoise",
    "Sulcata Tortoise", "Yellow-Bellied Slider",
])

MIXED = "Mixed breed / Not sure"
BREEDS = {
    "Dog": DOG_BREEDS,
    "Cat": CAT_BREEDS,
    "Rabbit": RABBIT_BREEDS,
    "Bird": BIRD_BREEDS,
    "Hamster": HAMSTER_BREEDS,
    "Guinea Pig": GUINEA_PIG_BREEDS,
    "Turtle": TURTLE_BREEDS,
}
