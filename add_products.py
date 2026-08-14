import requests, json, re, os, urllib.request, ssl, shutil

def generate_desc(name, offer_id):
    """Generate a short product description in Russian"""
    offer = offer_id.lower()
    if 'овощерезка' in offer:
        return "Многофункциональная ручная овощерезка для овощей и фруктов. Несколько насадок в комплекте."
    elif 'ведро' in offer and 'крышка' in offer:
        return "Складное ведро с крышкой, 5 литров. Компактное хранение, прочный материал."
    elif 'ведро' in offer:
        return "Складное ведро, 10 литров. Компактное хранение, прочный материал."
    elif 'таз' in offer:
        return "Набор складных тазов. Компактное хранение, прочный материал."
    elif 'штопор' in offer:
        return "Штопор для бутылок. Надёжная конструкция, удобная ручка."
    elif 'чеснокодав' in offer:
        return "Чеснокодавилка-тёрка для чеснока, имбиря и орехов. Набор 2 шт."
    elif 'кист' in offer:
        return "Набор малярных кистей, 3 шт. Разные размеры: 50, 65, 75 мм."
    elif 'закаточн' in offer:
        return "Закаточная машинка для банок, автомат. Удобный ключ-закрутка."
    elif 'рулетка' in offer:
        return "Строительная рулетка с фиксатором. Прочный корпус, точная шкала."
    elif 'пассатиж' in offer:
        return "Пассатижи-плоскогубцы универсальные. Для дома, дачи и ремонта."
    else:
        return name

def fmt_price(p):
    return f"{p:,}".replace(",", " ")

repo_path = os.path.dirname(os.path.abspath(__file__))
img_dir = os.path.join(repo_path, 'images')

# Load OZON product info
info_path = 'C:/Users/ETOVEI/WorkBuddy/2026-08-14-09-52-57/ozon_products_info.json'
with open(info_path, 'r', encoding='utf-8') as f:
    ozon_products = json.load(f)

# Build product list
products = []
for p in ozon_products:
    sku = None
    for s in p.get('sources', []):
        if s.get('sku'):
            sku = str(s['sku'])
            break
    if not sku:
        continue

    name = p.get('name', '')
    price = p.get('price', '0')
    images = p.get('images', [])
    offer_id = p.get('offer_id', '')

    # Determine category
    offer_lower = offer_id.lower()
    if any(w in offer_lower for w in ['овощерезка', 'чеснокодав', 'штопор', 'закаточн']):
        cat_tag = 'Кухня'
    elif any(w in offer_lower for w in ['ведро', 'таз']):
        cat_tag = 'Для дома'
    elif any(w in offer_lower for w in ['рулетка', 'пассатиж', 'кисти', 'кисть']):
        cat_tag = 'Инструменты'
    else:
        cat_tag = 'Разное'

    # Calculate website prices (30% off OZON price)
    try:
        ozon_price = float(price)
    except:
        ozon_price = 0
    web_price = int(ozon_price * 0.7)
    web_old_price = int(ozon_price)

    products.append({
        'sku': sku,
        'name': name,
        'offer_id': offer_id,
        'price': fmt_price(web_price),
        'old_price': fmt_price(web_old_price),
        'images': images,
        'cat_tag': cat_tag,
        'desc': generate_desc(name, offer_id)
    })

print(f"Products to add: {len(products)}")

# Download images
ctx = ssl.create_default_context()
downloaded = 0
no_image = []

for p in products:
    sku = p['sku']
    img_path = os.path.join(img_dir, f"product_{sku}.jpg")

    if p['images']:
        img_url = p['images'][0]
        try:
            req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                with open(img_path, 'wb') as f:
                    f.write(resp.read())
            downloaded += 1
            print(f"  OK [{sku}] downloaded")
        except Exception as e:
            print(f"  FAIL [{sku}] {e}")
            no_image.append(sku)
    else:
        no_image.append(sku)
        print(f"  NO IMG [{sku}] {p['name'][:40]}")

# For products without images, use variant images
variant_map = {}
for p in products:
    prefix = p['offer_id'].split('_')[0] if '_' in p['offer_id'] else p['offer_id']
    if prefix not in variant_map:
        variant_map[prefix] = []
    variant_map[prefix].append(p)

for sku in no_image:
    target = next(p for p in products if p['sku'] == sku)
    prefix = target['offer_id'].split('_')[0] if '_' in target['offer_id'] else target['offer_id']
    for variant in variant_map.get(prefix, []):
        if variant['sku'] != sku and variant['images']:
            src_path = os.path.join(img_dir, f"product_{variant['sku']}.jpg")
            dst_path = os.path.join(img_dir, f"product_{sku}.jpg")
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)
                print(f"  COPY [{sku}] <- [{variant['sku']}]")
                break
    else:
        print(f"  NO VARIANT [{sku}] - placeholder")

print(f"\nDownloaded: {downloaded}, No image: {len(no_image)}")

# Generate HTML cards
html_cards = []
for p in products:
    card = f'''            <article class="product-card" data-category="other">
                <div class="product-image">
                    <img src="images/product_{p['sku']}.jpg" alt="{p['name']}" loading="lazy" onerror="if(this.dataset.retry){{this.parentElement.classList.add('img-error')}}else{{this.dataset.retry=1}}">
                    
                </div>
                <div class="product-info">
                    <span class="product-cat-tag">{p['cat_tag']}</span>
                    <h3 class="product-name">{p['name']}</h3>
                    <p class="product-desc">{p['desc']}</p>
                    <div class="product-footer">
                        <div class="price-block">
                            <span class="product-price">{p['price']} \u20bd</span>
                            <span class="product-old-price">{p['old_price']} \u20bd</span>
                        </div>
                        <a href="https://www.ozon.ru/product/{p['sku']}/" target="_blank" rel="noopener" class="btn btn-small add-to-cart" data-product="{p['name']}" data-price="{p['price']}">\u0412 \u043a\u043e\u0440\u0437\u0438\u043d\u0443</a>
                    </div>
                </div>
            </article>'''
    html_cards.append(card)

# Read HTML and insert cards
with open(os.path.join(repo_path, 'index.html'), 'r', encoding='utf-8') as f:
    html = f.read()

# Find insertion point - before "Каталог постоянно пополняется"
marker = 'Каталог постоянно пополняется'
insert_point = html.find(marker)

if insert_point > 0:
    cards_html = '\n'.join(html_cards) + '\n            '
    html = html[:insert_point] + cards_html + html[insert_point:]

    with open(os.path.join(repo_path, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    count = len(re.findall(r'<article class="product-card"', html))
    print(f"\nHTML updated! Total products on site: {count}")
else:
    print("ERROR: Could not find insertion point!")
