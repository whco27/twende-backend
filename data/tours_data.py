"""Default tours data for database initialization.

This module contains comprehensive tour data for the Twende Tours platform,
covering various safari experiences, beach getaways, and adventure tours
across Kenya and East Africa.

The data represents actual trip offerings that would typically be displayed
on the frontend and stored in the backend database.
"""

DEFAULT_TOURS = [
    # Safari Tours
    {
        'title': 'Masai Mara 3-Day Safari',
        'description': 'Experience the world-famous Masai Mara Game Reserve with expert guides. Witness the Great Migration and spot the Big Five in their natural habitat. Includes game drives, accommodation in luxury tented camps, and all meals.',
        'price': 45000.0,
        'duration': '3 days',
        'location': 'Masai Mara',
        'image_url': 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800',
        'available_slots': 20
    },
    {
        'title': 'Masai Mara Great Migration Special',
        'description': 'Witness one of nature\'s greatest spectacles - the Great Wildebeest Migration. See millions of wildebeest and zebras crossing the Mara River. This special tour runs during peak migration season (July-October).',
        'price': 75000.0,
        'duration': '5 days',
        'location': 'Masai Mara',
        'image_url': 'https://images.unsplash.com/photo-1547970810-dc1eac37d174?w=800',
        'available_slots': 15
    },
    {
        'title': 'Amboseli National Park Tour',
        'description': 'Enjoy breathtaking views of Mount Kilimanjaro while observing elephants and other wildlife in Amboseli. Known for its large elephant herds and stunning landscapes with Africa\'s highest peak as backdrop.',
        'price': 35000.0,
        'duration': '2 days',
        'location': 'Amboseli',
        'image_url': 'https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=800',
        'available_slots': 25
    },
    {
        'title': 'Amboseli Elephant Safari',
        'description': 'A specialized tour focused on Amboseli\'s famous elephant population. Get up close with large elephant families against the backdrop of Mount Kilimanjaro. Includes visit to local Maasai village.',
        'price': 42000.0,
        'duration': '3 days',
        'location': 'Amboseli',
        'image_url': 'https://images.unsplash.com/photo-1535941339077-2dd1c7963098?w=800',
        'available_slots': 18
    },
    {
        'title': 'Tsavo East & West Safari',
        'description': 'Explore Kenya\'s largest national park. See the famous red elephants, diverse landscapes, and Mzima Springs. This comprehensive tour covers both Tsavo East and Tsavo West parks.',
        'price': 55000.0,
        'duration': '4 days',
        'location': 'Tsavo',
        'image_url': 'https://images.unsplash.com/photo-1534177616064-ef1b8e0f4fa4?w=800',
        'available_slots': 18
    },
    {
        'title': 'Lake Nakuru Bird Watching',
        'description': 'Discover the pink flamingos and diverse bird species at Lake Nakuru. Also spot rhinos, lions, and leopards. Perfect day trip from Nairobi with stunning lake views.',
        'price': 22000.0,
        'duration': '1 day',
        'location': 'Lake Nakuru',
        'image_url': 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=800',
        'available_slots': 40
    },
    {
        'title': 'Lake Naivasha & Hell\'s Gate Adventure',
        'description': 'Visit the scenic Lake Naivasha for boat rides and hippo spotting, then explore Hell\'s Gate National Park on foot or by bicycle. See dramatic gorges, geothermal features, and wildlife.',
        'price': 18000.0,
        'duration': '1 day',
        'location': 'Lake Naivasha',
        'image_url': 'https://images.unsplash.com/photo-1489493887464-892be6d1daae?w=800',
        'available_slots': 35
    },
    {
        'title': 'Samburu National Reserve Safari',
        'description': 'Discover the unique wildlife of Northern Kenya including the Samburu Special Five: Grevy\'s zebra, Somali ostrich, reticulated giraffe, gerenuk, and beisa oryx. Cultural visits to Samburu communities included.',
        'price': 58000.0,
        'duration': '4 days',
        'location': 'Samburu',
        'image_url': 'https://images.unsplash.com/photo-1517430816045-df4b7de11d1d?w=800',
        'available_slots': 16
    },
    {
        'title': 'Ol Pejeta Conservancy Tour',
        'description': 'Visit the largest black rhino sanctuary in East Africa and home to the last two northern white rhinos. See chimpanzees at the Sweetwaters Chimpanzee Sanctuary.',
        'price': 32000.0,
        'duration': '2 days',
        'location': 'Ol Pejeta',
        'image_url': 'https://images.unsplash.com/photo-1503919545889-aef636e10ad4?w=800',
        'available_slots': 22
    },
    {
        'title': 'Nairobi National Park Half-Day Safari',
        'description': 'Experience a safari just minutes from Kenya\'s capital. Spot lions, rhinos, giraffes, and buffalo against the Nairobi skyline. Perfect for travelers with limited time.',
        'price': 8500.0,
        'duration': 'Half day',
        'location': 'Nairobi',
        'image_url': 'https://images.unsplash.com/photo-1523805009345-7448845a9e53?w=800',
        'available_slots': 50
    },
    
    # Beach & Coastal Tours
    {
        'title': 'Diani Beach Getaway',
        'description': 'Relax on the pristine white sands of Diani Beach. Enjoy water sports, snorkeling, and coastal Swahili cuisine. Consistently rated as one of Africa\'s best beaches.',
        'price': 28000.0,
        'duration': '4 days',
        'location': 'Diani Beach',
        'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800',
        'available_slots': 30
    },
    {
        'title': 'Watamu Marine Adventure',
        'description': 'Explore the beautiful Watamu Marine National Park. Snorkel among colorful coral reefs, swim with sea turtles, and visit the historic Gede Ruins.',
        'price': 35000.0,
        'duration': '4 days',
        'location': 'Watamu',
        'image_url': 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800',
        'available_slots': 25
    },
    {
        'title': 'Lamu Island Heritage Tour',
        'description': 'Step back in time on Lamu Island, a UNESCO World Heritage Site. Experience Swahili culture, explore ancient streets, and relax on pristine beaches. Includes dhow sailing trip.',
        'price': 48000.0,
        'duration': '4 days',
        'location': 'Lamu',
        'image_url': 'https://images.unsplash.com/photo-1590523741831-ab7e8b8f9c7f?w=800',
        'available_slots': 20
    },
    {
        'title': 'Mombasa City & Beach Tour',
        'description': 'Explore Mombasa\'s rich history including Fort Jesus, the Old Town, and beautiful North Coast beaches. Experience the coastal city\'s unique blend of African, Arab, and Portuguese influences.',
        'price': 25000.0,
        'duration': '3 days',
        'location': 'Mombasa',
        'image_url': 'https://images.unsplash.com/photo-1590060816668-c2e2eb92ad14?w=800',
        'available_slots': 28
    },
    {
        'title': 'Malindi & Gede Ruins Explorer',
        'description': 'Discover the historic town of Malindi and the mysterious Gede Ruins. Visit Vasco da Gama Pillar, the Marine Park, and enjoy fresh seafood on the beach.',
        'price': 22000.0,
        'duration': '2 days',
        'location': 'Malindi',
        'image_url': 'https://images.unsplash.com/photo-1518509562904-e7ef99cdcc86?w=800',
        'available_slots': 30
    },
    
    # Mountain & Adventure Tours
    {
        'title': 'Mount Kenya Hiking Adventure',
        'description': 'Conquer Africa\'s second-highest peak. This challenging trek offers stunning views and unique alpine ecosystems. Choose from several routes including the popular Sirimon and Chogoria trails.',
        'price': 65000.0,
        'duration': '5 days',
        'location': 'Mount Kenya',
        'image_url': 'https://images.unsplash.com/photo-1489493887464-892be6d1daae?w=800',
        'available_slots': 15
    },
    {
        'title': 'Mount Longonot Day Hike',
        'description': 'Hike to the rim of Mount Longonot, an extinct volcano in the Rift Valley. Enjoy panoramic views of the surrounding plains and walk around the crater rim.',
        'price': 6500.0,
        'duration': '1 day',
        'location': 'Mount Longonot',
        'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800',
        'available_slots': 45
    },
    {
        'title': 'Aberdare National Park Trek',
        'description': 'Explore the misty moorlands and dense forests of the Aberdares. Spot elephants, buffalo, and rare bongo antelopes. Visit spectacular waterfalls and stay at the famous Treetops Lodge.',
        'price': 38000.0,
        'duration': '3 days',
        'location': 'Aberdare',
        'image_url': 'https://images.unsplash.com/photo-1486299267070-83823f5448dd?w=800',
        'available_slots': 20
    },
    {
        'title': 'Kilimanjaro View Trek',
        'description': 'A scenic trek through the foothills near Mount Kilimanjaro. Perfect for those who want stunning mountain views without the full climb. Includes cultural visits to local Chagga villages.',
        'price': 28000.0,
        'duration': '3 days',
        'location': 'Kilimanjaro Foothills',
        'image_url': 'https://images.unsplash.com/photo-1521150932951-303a95503ed3?w=800',
        'available_slots': 22
    },
    
    # Cultural Tours
    {
        'title': 'Maasai Village Cultural Experience',
        'description': 'Immerse yourself in the rich culture of the Maasai people. Visit a traditional village, learn about their customs, participate in ceremonies, and witness traditional dances.',
        'price': 12000.0,
        'duration': '1 day',
        'location': 'Kajiado',
        'image_url': 'https://images.unsplash.com/photo-1523805009345-7448845a9e53?w=800',
        'available_slots': 35
    },
    {
        'title': 'Karen Blixen Museum & Giraffe Centre',
        'description': 'Visit the former home of Out of Africa author Karen Blixen, now a museum. Then head to the Giraffe Centre to feed endangered Rothschild giraffes.',
        'price': 5500.0,
        'duration': 'Half day',
        'location': 'Nairobi',
        'image_url': 'https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=800',
        'available_slots': 60
    },
    {
        'title': 'Nairobi City Tour',
        'description': 'Explore Kenya\'s vibrant capital. Visit the National Museum, Railway Museum, Uhuru Gardens, and experience the city\'s bustling markets and diverse cuisine.',
        'price': 7500.0,
        'duration': '1 day',
        'location': 'Nairobi',
        'image_url': 'https://images.unsplash.com/photo-1611348524140-53c9a25263d6?w=800',
        'available_slots': 50
    },
    
    # Multi-Day Safari Combinations
    {
        'title': 'Kenya Classic Safari - Big Five Tour',
        'description': 'The ultimate Kenyan safari experience covering Masai Mara, Lake Nakuru, and Amboseli. Guaranteed Big Five sightings with experienced guides and luxury accommodation.',
        'price': 125000.0,
        'duration': '7 days',
        'location': 'Multiple Parks',
        'image_url': 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800',
        'available_slots': 12
    },
    {
        'title': 'Northern Kenya Explorer',
        'description': 'Discover the wild and remote landscapes of Northern Kenya. Visit Samburu, Buffalo Springs, and the shores of Lake Turkana. Experience authentic nomadic cultures.',
        'price': 98000.0,
        'duration': '6 days',
        'location': 'Northern Kenya',
        'image_url': 'https://images.unsplash.com/photo-1517430816045-df4b7de11d1d?w=800',
        'available_slots': 14
    },
    {
        'title': 'Safari & Beach Combo',
        'description': 'The best of both worlds! Start with a 4-day Masai Mara safari, then fly to the coast for 3 days of beach relaxation in Diani. Internal flights included.',
        'price': 145000.0,
        'duration': '7 days',
        'location': 'Masai Mara & Diani',
        'image_url': 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800',
        'available_slots': 10
    },
    {
        'title': 'Rift Valley Lakes Tour',
        'description': 'Explore the stunning Rift Valley lakes: Nakuru for flamingos, Naivasha for hippos, and Bogoria for hot springs. A photographer\'s paradise with diverse birdlife.',
        'price': 48000.0,
        'duration': '3 days',
        'location': 'Rift Valley',
        'image_url': 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=800',
        'available_slots': 24
    },
    
    # Budget Tours
    {
        'title': 'Budget Masai Mara Safari',
        'description': 'Experience the Masai Mara on a budget! Stay in comfortable budget camps while enjoying full game drives. All meals and park fees included.',
        'price': 28000.0,
        'duration': '3 days',
        'location': 'Masai Mara',
        'image_url': 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800',
        'available_slots': 30
    },
    {
        'title': 'Nakuru & Naivasha Budget Tour',
        'description': 'A budget-friendly two-day trip to see flamingos at Lake Nakuru and enjoy a boat ride at Lake Naivasha. Perfect for weekend getaways.',
        'price': 15000.0,
        'duration': '2 days',
        'location': 'Nakuru & Naivasha',
        'image_url': 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=800',
        'available_slots': 40
    },
    
    # Luxury Tours
    {
        'title': 'Luxury Masai Mara Flying Safari',
        'description': 'Experience the Mara in ultimate luxury. Fly from Nairobi, stay in exclusive camps with private guides. Includes hot air balloon safari and bush dining.',
        'price': 285000.0,
        'duration': '4 days',
        'location': 'Masai Mara',
        'image_url': 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800',
        'available_slots': 8
    },
    {
        'title': 'Kenya Luxury Grand Tour',
        'description': 'The ultimate Kenya experience. Visit Masai Mara, Amboseli, and Samburu with stays in Kenya\'s finest lodges. Private vehicles and expert guides throughout.',
        'price': 450000.0,
        'duration': '10 days',
        'location': 'Multiple Parks',
        'image_url': 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800',
        'available_slots': 6
    },
]

# Validate all tours have required fields
def validate_tours_data(tours):
    """Validate that all tours have required fields."""
    required_fields = ['title', 'description', 'price', 'duration', 'location']
    for i, tour in enumerate(tours):
        for field in required_fields:
            if field not in tour:
                raise ValueError(f"Tour at index {i} missing required field: {field}")
        if tour['price'] <= 0:
            raise ValueError(f"Tour '{tour['title']}' has invalid price: {tour['price']}")
    return True

# Run validation on import
validate_tours_data(DEFAULT_TOURS)
