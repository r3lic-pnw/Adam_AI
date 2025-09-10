# Comprehensive Minecraft Guide for AI Agent

## Table of Contents
1. [Game Fundamentals](#game-fundamentals)
2. [World Structure and Biomes](#world-structure-and-biomes)
3. [Essential Items and Materials](#essential-items-and-materials)
4. [Basic Actions and Interactions](#basic-actions-and-interactions)
5. [Crafting System](#crafting-system)
6. [Resource Management](#resource-management)
7. [Survival Mechanics](#survival-mechanics)
8. [Building and Construction](#building-and-construction)
9. [Combat and Defense](#combat-and-defense)
10. [Mining and Exploration](#mining-and-exploration)
11. [Farming and Food](#farming-and-food)
12. [Progression and Goals](#progression-and-goals)
13. [Common Decision Trees](#common-decision-trees)
14. [API-Specific Considerations](#api-specific-considerations)

## Game Fundamentals

### Core Game Loop
Minecraft is a sandbox survival game where the primary objectives are:
- Gather resources from the environment
- Craft tools and items to improve efficiency
- Build shelter for protection
- Survive hostile mobs that spawn in darkness
- Progress through different material tiers (wood → stone → iron → diamond → netherite)

### Time System
- Each Minecraft day lasts 20 minutes (1200 seconds)
- Daylight lasts 10 minutes, night lasts 7 minutes, with 3 minutes of dawn/dusk
- Hostile mobs spawn in darkness (light level < 8)
- Safe to work outside during day, seek shelter at night

### Coordinate System
- X-axis: East (positive) and West (negative)
- Y-axis: Up (positive) and Down (negative), sea level is Y=64
- Z-axis: South (positive) and North (negative)
- Always track your base coordinates for navigation

## World Structure and Biomes

### World Layers (Y-Coordinates)
- **Y 320-384**: Build height limit
- **Y 200-320**: Mountain peaks, sky
- **Y 64-200**: Surface terrain
- **Y 0-64**: Underground, caves
- **Y -64 to 0**: Deep underground, deepslate
- **Y -64**: Bedrock level (lowest point)

### Common Biomes and Resources
- **Plains**: Wheat seeds, villages, horses, passive mobs
- **Forest**: Wood (oak, birch), animals, mushrooms
- **Mountains**: Stone, coal, iron, emeralds at higher altitudes
- **Desert**: Sand, sandstone, villages, temples
- **Ocean**: Fish, kelp, ocean monuments, drowned mobs
- **Caves**: Most valuable ores, hostile mobs, underground lakes

### Important Structures
- **Villages**: Trade with villagers, free loot, beds
- **Dungeons**: Mob spawners, valuable loot chests
- **Mineshafts**: Rails, wood, cave spider spawners
- **Strongholds**: End portals, libraries, valuable loot

## Essential Items and Materials

### Tool Materials (Efficiency Order)
1. **Wood**: 2x faster than hand, 59 durability
2. **Stone**: 4x faster than hand, 131 durability
3. **Iron**: 6x faster than hand, 250 durability
4. **Diamond**: 8x faster than hand, 1561 durability
5. **Netherite**: 9x faster than hand, 2031 durability

### Critical Early Game Items
- **Wooden Pickaxe**: Mine stone and coal
- **Stone Pickaxe**: Mine iron ore
- **Iron Pickaxe**: Mine diamonds and redstone
- **Furnace**: Smelt ores, cook food
- **Crafting Table**: Access 3x3 crafting recipes
- **Chest**: Store items (27 slots)
- **Bed**: Set spawn point, skip night

### Essential Materials List
- **Wood**: Building, crafting tables, tools, fuel
- **Stone**: Tools, building, furnace ingredient
- **Coal**: Primary fuel source, torches
- **Iron**: Tools, armor, buckets, rails
- **Food**: Any meat, bread, potatoes, carrots
- **String**: Bow crafting, leads, fishing rods

## Basic Actions and Interactions

### Movement Actions
- **Walk**: Standard movement speed
- **Sprint**: 30% faster, drains hunger
- **Jump**: Clear 1-block heights
- **Crouch**: Prevents falling off edges, quieter movement
- **Swim**: Move through water, requires air management

### Block Interactions
- **Break Block**: Hold attack button, different tools have different speeds
- **Place Block**: Right-click with block in hand
- **Interact**: Right-click on chests, furnaces, doors, buttons
- **Mine Efficiency**: Always use correct tool for faster mining

### Inventory Management
- **Inventory Size**: 36 slots (27 main + 9 hotbar)
- **Stack Sizes**: Most blocks stack to 64, tools don't stack
- **Quick Transfer**: Shift+click to move items quickly
- **Drop Items**: Q key or drag outside inventory

## Crafting System

### Crafting Table Recipes (Most Important)

#### Tools
- **Wooden Pickaxe**: 3 wood planks + 2 sticks (T-shape)
- **Stone Pickaxe**: 3 cobblestone + 2 sticks (T-shape)
- **Iron Pickaxe**: 3 iron ingots + 2 sticks (T-shape)
- **Axe**: 3 material + 2 sticks (L-shape, left side)
- **Shovel**: 1 material + 2 sticks (vertical line)
- **Sword**: 2 material + 1 stick (vertical line)

#### Essential Items
- **Crafting Table**: 4 wood planks (2x2)
- **Furnace**: 8 cobblestone (hollow square)
- **Chest**: 8 wood planks (hollow square)
- **Sticks**: 2 wood planks (vertical)
- **Torch**: 1 coal/charcoal + 1 stick (vertical)
- **Bed**: 3 wool + 3 wood planks

#### Food
- **Bread**: 3 wheat (horizontal line)
- **Mushroom Stew**: 1 red mushroom + 1 brown mushroom + 1 bowl

### Smelting Recipes
- **Iron Ingot**: Iron ore + fuel
- **Glass**: Sand + fuel
- **Charcoal**: Wood logs + fuel
- **Stone**: Cobblestone + fuel
- **Cooked Meat**: Raw meat + fuel

## Resource Management

### Fuel Efficiency
1. **Lava Bucket**: 1000 seconds (best for automation)
2. **Coal Block**: 800 seconds
3. **Blaze Rod**: 120 seconds
4. **Coal/Charcoal**: 80 seconds each
5. **Wood items**: 15 seconds each

### Storage Organization
- **Early Game**: Single chest near crafting area
- **Mid Game**: Multiple chests by category (tools, blocks, food, misc)
- **Late Game**: Item sorting systems with hoppers

### Inventory Priorities (Hotbar)
1. Pickaxe (primary tool)
2. Weapon (sword)
3. Food (cooked meat/bread)
4. Torches (light source)
5. Building blocks (cobblestone/wood)
6. Axe/Shovel (situational tools)
7. Water bucket (safety/utility)
8. Bow and arrows (ranged combat)

## Survival Mechanics

### Health System
- **20 Health Points** (10 hearts displayed)
- **Regeneration**: Requires food bar above 18/20
- **Damage Sources**: Mobs, fall damage, drowning, lava, starvation

### Hunger System
- **20 Hunger Points** (10 drumsticks displayed)
- **Saturation**: Hidden stat that delays hunger loss
- **Effects of Low Hunger**:
  - Below 18: No health regeneration
  - Below 6: Cannot sprint
  - At 0: Take starvation damage

### Best Foods (Hunger + Saturation)
1. **Golden Carrot**: 6 hunger, 14.4 saturation
2. **Steak/Pork Chop**: 8 hunger, 12.8 saturation
3. **Bread**: 5 hunger, 6 saturation
4. **Cooked Chicken**: 6 hunger, 7.2 saturation

### Lighting and Mob Spawning
- **Light Level 0-7**: Hostile mobs can spawn
- **Light Level 8+**: Prevents hostile mob spawning
- **Torch Placement**: Every 7 blocks prevents spawning
- **Safe Lighting**: Place torches in patterns to cover all dark areas

## Building and Construction

### Basic Shelter Requirements
- **Walls**: Any solid block, height of 2+ blocks
- **Roof**: Prevents mob spawning on top
- **Door**: Wooden door for entry (iron door needs redstone)
- **Lighting**: Torches inside to prevent mob spawning
- **Bed**: Sets respawn point

### Common Building Blocks
- **Cobblestone**: Abundant, blast-resistant, fire-proof
- **Wood Planks**: Renewable, flammable, various colors
- **Stone Bricks**: Decorative, crafted from stone
- **Glass**: Transparent, allows light, fragile

### Building Tips
- **Foundation**: Start with a flat area or create one
- **Scale**: Count blocks - typical room is 5x5x3 minimum
- **Symmetry**: Plan before building for better aesthetics
- **Functionality**: Include storage, crafting area, bed

## Combat and Defense

### Hostile Mobs (Threats)
- **Zombie**: 20 HP, slow, burns in sunlight, breaks doors on hard
- **Skeleton**: 20 HP, ranged bow attacks, burns in sunlight
- **Creeper**: 20 HP, explodes when close (destroys blocks)
- **Spider**: 16 HP, neutral in daylight, climbs walls
- **Enderman**: 40 HP, teleports, don't look directly at them

### Combat Strategies
- **Melee**: Attack then back away to avoid damage
- **Ranged**: Bow and arrows for safer combat
- **Environmental**: Use height advantage, water, lava
- **Shields**: Block attacks and projectiles (1 iron + 6 planks)

### Defense Priorities
1. **Lighting**: Prevent mob spawning near base
2. **Walls**: 2+ block high walls around base
3. **Roof**: Prevent spider climbing over walls
4. **Multiple Exits**: Don't get trapped inside

## Mining and Exploration

### Mining Strategies
- **Surface Mining**: Gather exposed ores, minimal danger
- **Cave Exploration**: High ore density, many hostile mobs
- **Strip Mining**: Systematic mining at specific Y-levels
- **Branch Mining**: Main tunnel with side branches

### Optimal Mining Levels
- **Y 58-62**: General mining, avoid lava lakes
- **Y 11-15**: Diamond mining (most common at Y 11-12)
- **Y -58 to -54**: Best for diamonds in new terrain
- **Y 15**: Redstone mining
- **Y 32**: Gold mining

### Mining Safety
- **Always carry**: Pickaxe, torches, food, weapon
- **Mark your path**: Torches on right wall when entering
- **Avoid digging straight down**: Risk of falling into lava/void
- **Listen for mobs**: Stop mining to hear nearby threats
- **Emergency items**: Water bucket, blocks to build up

### Ore Distribution and Uses
- **Coal**: Y 5-50, fuel and torches
- **Iron**: Y -16 to 112, tools and armor
- **Gold**: Y -16 to 32, powered rails and golden apples
- **Diamond**: Y -64 to 16, best tools and armor
- **Redstone**: Y -64 to 16, circuits and mechanisms

## Farming and Food

### Crop Farming Basics
- **Farmland**: Hoe grass blocks near water
- **Water Source**: Within 4 blocks of farmland
- **Light Level**: 9+ for crop growth
- **Bone Meal**: Instantly grows crops

### Essential Crops
- **Wheat**: Bread crafting, breed cows/sheep/pigs
- **Carrots**: Direct food, breed pigs
- **Potatoes**: Direct food when cooked
- **Sugar Cane**: Paper for books, sugar for cakes

### Animal Farming
- **Breeding Requirements**: Feed two adults same food type
- **Cows**: Wheat → Leather, milk, beef
- **Pigs**: Carrots/potatoes → Pork
- **Chickens**: Seeds → Eggs, feathers, chicken meat
- **Sheep**: Wheat → Wool, mutton

### Fishing
- **Requirements**: Fishing rod + water body
- **Catches**: Fish (food), enchanted books, treasure
- **Time**: Varies, watch for bobber to sink

## Progression and Goals

### Early Game Progression (Day 1-3)
1. **Immediate**: Punch trees, make wooden tools
2. **Hour 1**: Build crafting table, make stone tools
3. **Day 1**: Find/dig shelter, make bed, gather food
4. **Day 2**: Mine for coal and iron, improve tools
5. **Day 3**: Establish base, organize storage, explore locally

### Mid Game Goals (Day 4-20)
1. **Iron Age**: Full iron tools and armor
2. **Secure Base**: Well-lit, organized, defended
3. **Food Security**: Sustainable farm or animal breeding
4. **Local Mapping**: Know surrounding area and resources
5. **Diamond Tools**: At least diamond pickaxe and sword

### Late Game Objectives (Day 20+)
1. **Diamond/Netherite Gear**: Best equipment
2. **Nether Access**: Portal construction and exploration
3. **Enchanting Setup**: Enchanting table and bookshelves
4. **Advanced Builds**: Complex redstone, large structures
5. **End Game**: Dragon fight, elytra, end cities

## Common Decision Trees

### When to Mine vs. Explore
**Mine When**:
- Need specific resources (iron, diamonds)
- Have adequate food and tools
- Base is secure and well-stocked
- Daylight hours remaining for safe return

**Explore When**:
- Need new biomes or structures
- Looking for villages or loot
- Searching for specific materials (sand, clay)
- Have backup equipment in case of death

### Day vs. Night Activities
**Day Activities**:
- Surface exploration and travel
- Building and construction outside
- Hunting animals for food
- Long-distance mining expeditions

**Night Activities**:
- Underground mining (caves are always dark)
- Indoor crafting and organizing
- Base improvement and decoration
- Short mining sessions near base

### Resource Priority Decisions
**High Priority**: Food, tools, fuel (coal), building materials
**Medium Priority**: Armor, weapons, decorative blocks
**Low Priority**: Rare materials for late-game items

### Emergency Protocols
**If Low on Health**: Find safe area, eat food above 18 hunger
**If Lost**: Build tall tower, place torches, note coordinates
**If Mob Swarm**: Retreat to high ground or enclosed space
**If Equipment Broken**: Return to base immediately with backup tools

## API-Specific Considerations

### Action Planning
- **Batch Operations**: Plan multiple related actions together
- **State Awareness**: Always know health, hunger, inventory status
- **Error Handling**: Have backup plans for failed actions
- **Resource Tracking**: Monitor tool durability and inventory space

### Pathfinding Considerations
- **Obstacle Avoidance**: Water, lava, cliffs, mob spawners
- **Efficient Routes**: Minimize travel time and distance
- **Safety Margins**: Avoid paths that lead near dangerous areas
- **Landmark Navigation**: Use distinct blocks or structures as waypoints

### Optimal Bot Behavior Patterns
1. **Morning Routine**: Check inventory, repair tools, plan day's activities
2. **Resource Gathering**: Focus on most needed materials first
3. **Safety Checks**: Monitor health/hunger every 5-10 actions
4. **Evening Return**: Head back to base before nightfall
5. **Night Activities**: Safe indoor tasks or well-lit mining

### Decision Timing
- **Tool Crafting**: When current tool reaches <25% durability
- **Food Consumption**: When hunger drops below 16/20
- **Base Return**: When inventory >75% full or health <50%
- **Sleep Decision**: When night falls and no urgent tasks

### Multi-Step Task Management
1. **Gather Materials**: List all required items before starting
2. **Prepare Workspace**: Clear crafting area, organize materials
3. **Execute Sequentially**: Complete each step before moving to next
4. **Verify Completion**: Check that intended result was achieved
5. **Clean Up**: Store excess materials, repair/replace tools

This guide provides comprehensive information for decision-making in Minecraft. Each section can be used independently as context for specific situations the agent encounters.