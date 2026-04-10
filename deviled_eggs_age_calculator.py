"""
Deviled Eggs Age Converter
Convert a person's age to deviled eggs using population consumption data,
shelf life, and life expectancy.
"""

def calculate_deviled_eggs_age(
    user_age,
    eggs_per_year=30,
    shelf_life_days=4,
    life_expectancy=78
):
    """
    Calculate a person's age in deviled eggs.
    
    Formula: Age in Eggs = (user_age * eggs_per_year * 365) / shelf_life_days / life_expectancy
    
    Args:
        user_age: Person's age in years
        eggs_per_year: Average deviled eggs consumed per person per year (default: 30)
        shelf_life_days: Days deviled eggs stay fresh (default: 4)
        life_expectancy: Average human lifespan in years (default: 78)
    
    Returns:
        Dictionary with calculated values and breakdown
    """
    
    # Calculate total eggs consumed in user's lifetime
    total_eggs_lifetime = eggs_per_year * life_expectancy
    
    # Calculate how many "batches" of eggs exist in a year (365 / shelf_life)
    batches_per_year = 365 / shelf_life_days
    
    # Age in deviled eggs: proportion of life × total lifetime eggs × batches per year
    age_in_eggs = (user_age / life_expectancy) * total_eggs_lifetime * batches_per_year
    
    return {
        "age_in_eggs": round(age_in_eggs, 2),
        "total_eggs_lifetime": total_eggs_lifetime,
        "batches_per_year": round(batches_per_year, 2),
        "breakdown": {
            "user_age": user_age,
            "eggs_per_year": eggs_per_year,
            "shelf_life_days": shelf_life_days,
            "life_expectancy": life_expectancy
        }
    }


def interactive_calculator():
    """Interactive mode for the deviled eggs age calculator."""
    
    print("=" * 60)
    print("🥚 DEVILED EGGS AGE CONVERTER 🥚")
    print("=" * 60)
    print()
    
    # Get user age
    while True:
        try:
            age = float(input("Enter your age (in years): "))
            if age < 0 or age > 150:
                print("Please enter a realistic age (0-150).")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    print()
    print("Using default parameters:")
    print("  • Average eggs consumed per person per year: 30")
    print("  • Deviled eggs shelf life: 4 days")
    print("  • Average life expectancy: 78 years")
    print()
    
    customize = input("Customize these parameters? (y/n): ").strip().lower()
    
    params = {
        "eggs_per_year": 30,
        "shelf_life_days": 4,
        "life_expectancy": 78
    }
    
    if customize == 'y':
        try:
            eggs_per_year = input("Eggs per person per year [30]: ").strip()
            params["eggs_per_year"] = float(eggs_per_year) if eggs_per_year else 30
            
            shelf_life = input("Shelf life in days [4]: ").strip()
            params["shelf_life_days"] = float(shelf_life) if shelf_life else 4
            
            life_exp = input("Life expectancy in years [78]: ").strip()
            params["life_expectancy"] = float(life_exp) if life_exp else 78
        except ValueError:
            print("Invalid input. Using default parameters.")
    
    print()
    print("-" * 60)
    
    result = calculate_deviled_eggs_age(age, **params)
    
    print()
    print(f"✨ YOUR AGE IN DEVILED EGGS: {result['age_in_eggs']} eggs")
    print()
    print("Breakdown:")
    print(f"  Real age: {age} years")
    print(f"  Eggs/year consumption: {params['eggs_per_year']} eggs")
    print(f"  Shelf life: {params['shelf_life_days']} days")
    print(f"  Life expectancy: {params['life_expectancy']} years")
    print(f"  Total eggs in lifetime: {result['total_eggs_lifetime']} eggs")
    print(f"  Batches per year: {result['batches_per_year']}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    interactive_calculator()
