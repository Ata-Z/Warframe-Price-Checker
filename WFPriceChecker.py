import asyncio
from playwright.async_api import async_playwright
from asyncio import Semaphore
from datetime import datetime
import time


mods = [
    'primed_continuity', 'transient_fortitude', 'primed_flow', 'blind_rage', 'primed_ravage', 
    'primed_ammo_stock', 'primed_bane_of_corpus', 'primed_bane_of_grineer', 'primed_bane_of_infested',
    'primed_bane_of_corrupted', 'primed_animal_instinct', 'primed_redirection', 'primed_reach',
    'primed_regen', 'primed_rubedo_lined_barrel', 'primed_charged_shell', 'primed_chilling_grasp',  
    'primed_cleanse_corpus', 'primed_cleanse_grineer', 'primed_cleanse_infested', 'primed_cleanse_corrupted',
    'primed_convulsion', 'primed_cryo_rounds', 'primed_deadly_efficiency', 'primed_dual_rounds',
    'primed_expel_corpus', 'primed_expel_grineer', 'primed_expel_infested', 'primed_expel_corrupted',
    'primed_fast_hands', 'primed_fever_strike', 'primed_firestorm', 'primed_fulmination',
    'primed_heated_charge', 'primed_heavy_trauma', 'primed_magazine_warp', 'primed_morphic_transformer',
    'primed_pack_leader', 'primed_pistol_ammo_mutation', 'primed_pistol_gambit', 'primed_point_blank',
    'primed_pressure_point', 'primed_quickdraw', 'primed_rifle_ammo_mutation', 'primed_shotgun_ammo_mutation',
    'primed_slip_magazine', 'primed_smite_corpus', 'primed_smite_grineer', 'primed_smite_infested',
    'primed_smite_corrupted', 'primed_sniper_ammo_mutation', 'primed_tactical_pump', 'primed_target_cracker',
    'galvanized_aptitude','galvanized_acceleration','galvanized_chamber','galvanized_crosshairs','galvanized_diffusion',
    'galvanized_hell'
    
]


CONCURRENT_LIMIT = 10  

MAX_RETRIES = 3  
SHORT_TIMEOUT = 15000  
LONG_TIMEOUT = 30000  


async def scrape_mod(mod, semaphore, context):
    # Scrapes seller and buyer prices for a given mod with retry logic
    url = f'https://warframe.market/items/{mod}'
    async with semaphore:  # Control concurrency
        retries = 0
        while retries < MAX_RETRIES:
            try:
                page = await context.new_page()  
                start_time = time.time()
                print(f"[{datetime.now()}] Starting scrape for {mod} (Attempt {retries + 1})")

                
                await page.goto(url, timeout=LONG_TIMEOUT)
                await page.wait_for_load_state("networkidle", timeout=LONG_TIMEOUT)

               
                await page.wait_for_selector('[data-index="0"] .price--LQgqJ.sell--UxmH0 b', timeout=SHORT_TIMEOUT)
                seller_price_element = await page.query_selector('[data-index="0"] .price--LQgqJ.sell--UxmH0 b')
                seller_price = int((await seller_price_element.inner_text()).replace(',', '').strip())

                
                await page.click('label.btn.btn__primary--L8HyD.btn__radio--tcfEf.activeWtb--SEkhf.wtb')
                await page.wait_for_selector('[data-index="0"] .price--LQgqJ.buy--lHHVs b', timeout=SHORT_TIMEOUT)
                buyer_price_element = await page.query_selector('[data-index="0"] .price--LQgqJ.buy--lHHVs b')
                buyer_price = int((await buyer_price_element.inner_text()).replace(',', '').strip())

                
                profit = buyer_price - seller_price
                print(f"[{datetime.now()}] Scraped {mod}: Seller={seller_price}, Buyer={buyer_price}, Profit={profit}")
                return {"mod": mod, "seller_price": seller_price, "buyer_price": buyer_price, "profit": profit}

            except Exception as e:
                retries += 1
                print(f"[{datetime.now()}] Error scraping {mod} (Attempt {retries}): {e}")
                if retries == MAX_RETRIES:
                    print(f"[{datetime.now()}] Max retries reached for {mod}. Skipping.")
                    return None

            finally:
                if 'page' in locals():
                    await page.close()  

        
        print(f"[{datetime.now()}] Failed to scrape {mod} after {MAX_RETRIES} attempts.")
        return None


async def main():
    # Main function to scrape all mods concurrently.
    results = []
    semaphore = Semaphore(CONCURRENT_LIMIT)  

    start_program_time = time.time()  

    async with async_playwright() as playwright:
        
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()

        
        tasks = [scrape_mod(mod, semaphore, context) for mod in mods]

        
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        results = [res for res in responses if res is not None]

        
        failed_count = len([res for res in responses if res is None])

        sorted_results = sorted(results, key=lambda x: x["profit"], reverse=True)

        
        print("\nFinal Results:")
        for res in sorted_results:
            print(f"Mod: {res['mod']}, Seller: {res['seller_price']}p, Buyer: {res['buyer_price']}p, Profit: {res['profit']}p")

        
        await browser.close()

    
    total_program_time = time.time() - start_program_time
    print(f"\nProgram completed in {total_program_time:.2f} seconds")
    print(f"Number of failed mods: {failed_count}")


if __name__ == "__main__":
    asyncio.run(main())
