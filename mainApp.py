#!/usr/bin/python
# -*- encoding: utf-8 -*-
import MySQLdb
import requests
from lxml import etree,html
import re
from datetime import date,datetime
from time import sleep, time
import simplejson
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()

options.add_argument('--headless')
options.add_argument('--remote-debugging-port=9222')
options.add_argument('--no-sandbox')
options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36')
#from selenium import webdriver
#from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=options)

#s = requests
log_file = open("logs.txt","a")
db = MySQLdb.connect("----localhost----","----user----","-----PASSWORD-----","scrap")
#print(db)
cursor = db.cursor()


def logWrite(text):
	log_file.write("["+str(date.today().strftime("%d/%m/%Y")) + "]-" + "Amazon warning" + "-" + text+'\n')

def scrapeAmazon(amazonURL):
	amazonASIN = re.findall(r'dp/([^/]+)',amazonURL)
	try:

		driver.get(amazonURL)
		responseAmazon = driver.page_source

	except:
		responseAmazon = ""
		successCode = 0
		log_file.write("selenium crashed"+"\n")

	successCode = 0
	amazonStock = 0
	amazonPrice = 0
	amazon3rdStock = 0
	amazon3rdPrice = 0
	#print(responseAmazon.text)
	try:
		tree = html.fromstring(responseAmazon)
		mainTree = tree.xpath("//div[@id='histories']")

		try:
			amazonTitle = tree.xpath("//span[@id='productTitle']/text()")
			#print(amazonTitle)
			amazonTitle = amazonTitle[0].replace("\n","").replace("  ","")
		except:
			amazonTitle = ""

		try:
			amazonImg = tree.xpath("//img[contains(@src,'images-amazon.com/images/I/')]/@src")
			#for im in amazonImg:
				#print(im)
			temp = re.findall(r'images/I/([^.]+)',amazonImg[0])
			amazonImg = "https://images-na.ssl-images-amazon.com/images/I/"+temp[0]+".jpg"
			#print(amazonImg)
		except:
			amazonImg = ""

		try:
			amazonRating = tree.xpath("//*[@id='acrPopover']/@title")
			amazonRating = amazonRating[0].replace(" out of 5 stars","")
		except:
			amazonRating = ""

		sellerInfo = tree.xpath("//*[@id='merchant-info' and (contains(.,'amazon') or contains(.,'Amazon'))]/text()")
		availability = tree.xpath("//*[@id='availability']//text()")

		price = tree.xpath("//*[@id='priceblock_ourprice']/text()")
		if(price == []):
			amazonPrice = ""
			amazon3rdPrice = ""

		availCode = 0
		for avail in availability:
			if('in stock.' in avail.lower() or 'available now.' in avail.lower()):
				availCode = 1
			if('out of stock.' in avail.lower()):
				availCode = 0
				break

		if(len(sellerInfo) > 0):
			if(availCode == 1):
				amazonStock = 1
			else:
				amazonStock = 0
			try:
				amazonPrice = price[0].replace("\n","").replace("$","").replace(",","").replace(" ","")
			except:
				amazonPrice = ""

			amazon3rdStock = ""
			amazon3rdPrice = ""
		else:
			if(availCode == 1):
				amazon3rdStock = 1
			else:
				amazon3rdStock = 0
			try:
				amazon3rdPrice = price[0].replace("\n","").replace("$","").replace(",","").replace(" ","")
			except:
				amazon3rdPrice = ""

			amazonStock = ""
			amazonPrice = ""

		successCode = 1
	except Exception as e:
		#print(e)
		amazonTitle = ""
		amazonStock = 0
		amazon3rdStock = 0
		amazonPrice = 0
		amazon3rdPrice = 0
		amazonImg = ""
		amazonRating = ""

		log_file.write(str(e)+"~"+amazonURL+'\n')
		successCode = 0



	temp_dict = {'success':successCode,'source':'Amazon','url':amazonURL,'imgUrl':amazonImg,'title':amazonTitle,'stock1':amazonStock,'stock2':amazon3rdStock,'price1':amazonPrice,'price2':amazon3rdPrice,'rating':amazonRating}
	return(temp_dict)
	#return 0

def scrapeBB(bestBuyURL):
	bestBuyHeader = {
	'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'accept-encoding':'gzip, deflate, br',
	'accept-language':'en-US,en;q=0.9',
	'cache-control':'no-cache',
	#'cookie':'UID=b2803c74-cd2d-442b-92a3-a1305b08790d; bm_sz=AFBD559F2D33F330B59D9F2795D58B79~YAAQXNs4fXfA0sdxAQAAlB0J5wdyXIq6BMRaa+/vA56paoU501tc/5VUeyAzUQUcx/X6su1aArRS4b26p0slRoARRt9vOs+3ZsatbYgLVhnq16Z93418SNzl6fVe+TGeLVSGRCs2SsD67rvUZyw0pd6W0OqErRyHRqQUpXZU/HCzkwKJ0QX0oDOasw48SuAS6Q==; bby_rdp=l; CTT=5a1db5cf92e0a778939891f37f27093c; SID=1edb586b-9933-40e5-927d-9f33bb3054d4; bby_cbc_lb=p-browse-e; _abck=CAE87DBEEB132521FBC9D6D0145CD8C3~0~YAAQXNs4fXrA0sdxAQAA4CAJ5wMAohF1u4WRkOzNVvTScfKt68/+OMYWbqRZBGtDKqcXVI/uOey9cp+k7t+eJW0yK5FxbHxaSEyPTlk+7LYLbSWC92mTo+XcVe0MR5905OgmNoEKSe8KcEYmQDnlIPvDPiuLRleqs+joPBg98OyS41jeeZsjOYWrlbKaAeRsmyGxaROgipBYg0GPCQBE7XqnQAw7w7C9uwgAH8SpQGUdeatXFTCi3wlZUsLq3WNWIVZLL9sEOCFyvU6GpTaHMU6xOVbVERYwU2EG59zblIuflC5YI58K62sv3VVWHQdmjQO8AugdoIo=~-1~-1~-1; AMCVS_F6301253512D2BDB0A490D45%40AdobeOrg=1; s_cc=true; vt=e82c7904-8f22-11ea-9279-06174cc609d2; intl_splash=false; ltc=%20; oid=468879744; optimizelyEndUserId=oeu1588719087091r0.16560520147911806; COM_TEST_FIX=2020-05-05T22%3A51%3A28.154Z; bby_prc_lb=p-prc-w; basketTimestamp=1588719091396; c2=Computers%20%26%20Tablets%3A%20PC%20Gaming%3A%20Gaming%20Laptops%3A%20pdp; bby_loc_lb=p-loc-e; locDestZip=96939; locStoreId=852; pst2=852; s_sq=%5B%5BB%5D%5D; bby_shpg_lb=p-shpg-e; sc-location-v2=%7B%22meta%22%3A%7B%22CreatedAt%22%3A%222020-05-05T22%3A52%3A55.662Z%22%2C%22ModifiedAt%22%3A%222020-05-05T22%3A52%3A56.767Z%22%2C%22ExpiresAt%22%3A%222021-05-05T22%3A52%3A56.767Z%22%7D%2C%22value%22%3A%22%7B%5C%22physical%5C%22%3A%7B%5C%22zipCode%5C%22%3A%5C%2296939%5C%22%2C%5C%22source%5C%22%3A%5C%22A%5C%22%2C%5C%22captureTime%5C%22%3A%5C%222020-05-05T22%3A52%3A55.660Z%5C%22%7D%2C%5C%22store%5C%22%3A%7B%5C%22zipCode%5C%22%3A%5C%2296701%5C%22%2C%5C%22storeId%5C%22%3A852%2C%5C%22storeHydratedCaptureTime%5C%22%3A%5C%222020-05-05T22%3A52%3A56.766Z%5C%22%7D%2C%5C%22destination%5C%22%3A%7B%5C%22zipCode%5C%22%3A%5C%2296939%5C%22%7D%7D%22%7D; bby_ispu_lb=p-ispu-e; AMCV_F6301253512D2BDB0A490D45%40AdobeOrg=1585540135%7CMCMID%7C59272685614388970976192452522290225300%7CMCAID%7CNONE%7CMCOPTOUT-1588726378s%7CNONE%7CvVersion%7C4.4.0',
	'pragma':'no-cache',
	'referer':'https://www.google.com/',
	'sec-fetch-dest':'document',
	'sec-fetch-mode':'navigate',
	'sec-fetch-site':'same-origin',
	'sec-fetch-user':'?1',
	'upgrade-insecure-requests':'1',
	'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/81.0.4044.138 Safari/537.36'
	}
	bestBuyURL = bestBuyURL + "&intl=nosplash" ## aditional for access data
	responseCode = 999
	retryCount = 0
	while(responseCode != 200):
		try:
			responseBh = requests.get(bestBuyURL, headers = bestBuyHeader)
			responseCode = responseBh.status_code
		except:
			responseCode = 999
		#print(responseCode)
		if(responseCode !=200):
			sleep(5)
			print("Timeout")
			retryCount = retryCount + 1

		if(retryCount > 5):
			responseAmazon = ""
			break

	#rUrl = responseBh.url


	try:
		tree = html.fromstring(responseBh.text)
		try:
			bestBuyTitle = tree.xpath("//div[@itemprop='name']/h1/text()")
			bestBuyTitle = bestBuyTitle[0]
		except:
			bestBuyTitle = ""
		try:
			#bestBuyStock = tree.xpath("//div[@class='fulfillment-add-to-cart-button']//button[not (@disabled)]")
			#x = bestBuyStock[0].xpath("./text()")
			bestBuyStock = tree.xpath("//*[contains(@class,'add-to-cart-button') and contains(.,'Add to Cart')]/text()")
			#print(testz)
			#print(len(testz))
			if(len(bestBuyStock)==1):
				bestBuyStock = 1
			else:
				bestBuyStock = 0
		except:
			bestBuyStock = 0

		try:
			bestBuyPrice = tree.xpath("//div[@class='priceView-hero-price priceView-customer-price']/span/text()")
			bestBuyPrice = bestBuyPrice[0].replace("\n","").replace("$","").replace(",","").replace(" ","")
		except:
			bestBuyPrice = 0

		try:
			bestBuyImg = tree.xpath("//img[@class='primary-image']/@src")
			bestBuyImg = bestBuyImg[0]
		except:
			bestBuyImg = ""

		try:
			bestBuyRating = tree.xpath("//div[@class='user-generated-content-ugc-stats']//p[@class='sr-only']/following-sibling::i/@alt")
			bestBuyRating = bestBuyRating[0]
		except:
			bestBuyRating = ""
		successCode = 1

	except Exception as e:
		#print(e)
		bestBuyTitle = ""
		bestBuyStock = 0
		bestBuyPrice = 0
		bestBuyRating = ""
		bestBuyImg = ""

		log_file.write(str(e)+"~"+bestBuyURL+'\n')
		successCode = 0

	temp_dict = {'success':successCode,'source':'BestBuy','url':bestBuyURL,'imgUrl':bestBuyImg,'title':bestBuyTitle,'stock1':bestBuyStock,'stock2':"",'price1':bestBuyPrice,'price2':"",'rating':bestBuyRating}
	return(temp_dict)

def scrapeBH(bhURL):
	bhHeader = {
	'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	#'accept-encoding':'gzip, deflate, br',
	'accept-language':'en-US,en;q=0.9',
	'cache-control':'no-cache',
	#cookie':'__cfduid=d4a6d3283c2256d147ae066627468848e1588553795; sessionKey=722c6da5-0f7b-4d83-b264-792ba95aa0d9; mapp=0; aperture-be-commit-id=n/a; uui=800.606.6969%20/%20212.444.6615|; locale=en; cartId=17786720147; cookieID=198264983731588553796083; dcid=1588553796065-83884464; D_IID=6A6A237C-2C24-3531-B886-FF91CB0D1DCB; D_UID=AF85F5DD-FA20-3C65-90BB-6399F4146D65; D_ZID=A5517FFD-FE03-30AA-A268-B9AAA5162C71; D_ZUID=63C70FD0-3CA5-351B-B950-8D005C05C863; D_HID=A02D8135-4804-3C53-AFBA-A5C3ED8FE638; D_SID=139.194.87.54:77Dt4QW/GW0BIvlbEufTsdS6BNjWkOgAf+rWtNKiSnk; ftr_ncd=6; aperture-be-commit-id=n/a; ab_nglp=A; TS0188dba5=01ec39615fd4e6c164cb3159b9ac2d75b633ca2331495cbc7ab9e229efceb25a992b371e554de125ea74f003b17a68534e94194cae31236344a68c482e220a36279ce8d4ee355e3963c5e3e93b2b67fed318a1aa5f42dc44904dc7324f09dd396d15ec9089; build=20200507v10-20200507v10; utkn=1bbf01004e07068c37d5fa0e67188dc; dpi=cat=2,cur=USD,app=D,lang=E,view=L,lgdin=N,cache=release-WEB-20200507v10-BHJ-DVB23488-13; lpi=cat=2,cur=USD,app=D,lang=E,view=L,lgdin=N,cache=release-WEB-20200507v10-BHJ-DVB23488-13,ipp=24,view=L,sort=BS,priv=N,state=; __cfruid=461a56b0bb682555c8935ee08eb2cf22a765375b-1588884414; SSID_C=CACk3B0OAAAAAABEaK9eGezDIERor14CAAAAAAAAAAAAvnO0XgANyCrRAAMUSR0AvnO0XgEA; SSSC_C=333.G6822786602306366489.2|53546.1919252; my_cookie=!L/xuWaRpTsZlPFEedo8zpbpxrFtb+i/IVM39DJumiDl23w0+9o8F9HFN7yvUXyeksJmE1ejqPAv6Jod8fkW9gZaT18xJyw0zNkmvYK8Eu/P1Rd3J27pCntf3yEw2yJ2EdIETB0CMeGRubi+EUCpp7jBloW5PHqIp8oiYWMB0xVZgBmZLAJ2K+oS6UNybkc7Qka0WSKmFDg==; JSESSIONID=KTbw5B7vL1GXDQixk1QMTu2JvmbkyJGb!-7551078; __cf_bm=706019855188078126d56423ab18434c342d90fb-1588884414-1800-ATg60f+q70XvV327X4lOFqdIBRibyvAsvT3va3yPmMShSe6n4o3y1pLZ2dQkdW8WkV3RJrSf8IB+cv8beGkNQlc=; ssTest=53546%3A1919252; TopBarCart=0|0; TS01d628c4=01ec39615faba9a1927162573f9e05ace9147f8549e8e82234d892065a97e2f331487a0fdb675529047cb678333ace446f05993ea96d5e24e8a375e19af0c4cf0cd904bb586b4f2fe1deb60c48bec3d183582dced9dd8f0d5619634e2cc7695fb6b612c7cba4493f44cab247f4dc50d1e9165f35d41fcec2c674ebf62e7cc7010c3fc3df27d7aa4b1af4771ea689484bc5d1ba897366683dbfa70298e74f71235719331a4272d57eb658bb805ac11acdcdab8d53d4cb94f46dcea09b3769b2e1718b6e20cb246d89b00804a3d1e3e003829c1b4ab9629783185bf48a78b32080964e045027; ft_ld_1h=1588884457548; forterToken=dd943fcb5daf4f0492988a2e607a0e76_1588884468080__UDF43_6; SSRT_C=-nO0XgIDAA; SSPV_C=yO0AAAAAAAQADgAAAAAAAAAAAAQAAAAAAAAAAAAA; TS01e1f1fd=01ec39615fb0510e07842cf22d1fc2197f996d7290e8e82234d892065a97e2f331487a0fdb7c012ddb25228ff35adcbd0f5fe04523a7f7074d094aeea8873b7cfd2fc095d83b2097d848e2cee7ad22b758e8bdd418505dac145f231499a37a66c0c82ba1aeba2fb9be085e4c254bb3d0007fffd17d2a124dd672f00cfb02d5fc73af0174453b25dbd8e03b20ae8a28779146996003; app_cookie=1588884475; TS0188dba5_77=080f850069ab2800d215d26fb2f201a727582ae42955cf5c5cdaed72852676970991336af136d4148ed5d0adbbb84b17084ebc34e1824000fd9af2033a1feb910be156ad3566703f6632819d210506351addc2f3374017b47a172186e497ef32163f0a48a5617ece04de8dd2413e24383ac5181c7a09c355
	'pragma':'no-cache',
	'referer':'https://www.bhphotovideo.com/',
	'sec-fetch-dest':'document',
	'sec-fetch-mode':'navigate',
	'sec-fetch-site':'same-origin',
	'sec-fetch-user':'?1',
	'upgrade-insecure-requests':'1',
	'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/81.0.4044.138 Safari/537.36'
	}
	#responseBh = requests.get(bhURL, headers = bhHeader, timeout=None)
	#print(responseBh.text)
	#return 0
	responseCode = 999
	retryCount = 0
	while(responseCode != 200):
		try:
			responseBh = requests.get(bhURL, headers = bhHeader, timeout=None)
			responseCode = responseBh.status_code
			#print(responseCode)
		except:
			responseCode = 999

		if(responseCode !=200):
			sleep(5)
			print("Timeout")
			retryCount = retryCount + 1

		if(retryCount > 5):
			responseAmazon = ""
			break

	#rUrl = responseBh.url


	try:
		tree = html.fromstring(responseBh.text)
		try:
			bhTitle = tree.xpath("//*[@data-selenium='productTitle']/text()")
			bhTitle = bhTitle[0]
		except:
			bhTitle = ""
		try:
			bhStock = tree.xpath("//span[@data-selenium='stockStatus']/text()")
			if(bhStock[0]=="In Stock"):
				bhStock = 1
			else:
				bhStock = 0
		except:
			bhStock = 0

		try:
			bhPrice = tree.xpath("//*[@data-selenium='pricingPrice']/text()")
			bhPrice = bhPrice[0].replace("\n","").replace("$","").replace(",","").replace(" ","")
		except:
			bhPrice = 0

		try:
			bhImg = tree.xpath("//img[@data-selenium='inlineMediaMainImage']/@src")
			bhImg = bhImg[0]
		except:
			bhImg = ""

		try:
			bhRating1 = tree.xpath("//div[@data-selenium='ratingContainer']/svg")
			bhRating2 = tree.xpath("//div[@data-selenium='ratingContainer']/svg[contains(@class,'full')]")
			bhRating = len(bhRating2) + (len(bhRating1)-len(bhRating2))*0.5
			#print(bhRating)
		except:
			bhRating = ""
		successCode = 1

	except Exception as e:
		#print(e)
		bhTitle = ""
		bhStock = 0
		bhPrice = 0
		bhRating = ""
		bhImg = ""

		log_file.write(str(e)+"~"+bhURL+'\n')
		successCode = 0

	temp_dict = {'success':successCode,'source':'B&H','url':bhURL,'imgUrl':bhImg,'title':bhTitle,'stock1':bhStock,'stock2':"",'price1':bhPrice,'price2':"",'rating':bhRating}
	return(temp_dict)

def runAll(dbCode,source,links):
	if(source=="Bestbuy"):
		temp = scrapeBB(links)
	if(source=="Amazon"):
		temp = scrapeAmazon(links)
	if(source=="B&H"):
		temp = scrapeBH(links)
	print(temp)
	if("amazon" in links):
		keycode = re.findall(r'dp/([^/]+)',links)
		keycode = keycode[0]
		#print(keycode)
	else:
		keycode = links.replace("https://","").replace("http://","").replace("www.bhphotovideo.com/c/product","").replace("www.amazon.com","").replace("www.bestbuy.com/site","").replace("/","").strip()
		keycode = keycode[0:11]
	print(keycode)
	dateTimeNow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	#print(keycode)
	if(temp['stock1']==''):
		newStock = temp['stock2']
		print("ini stock 2")
	else:
		newStock = temp['stock1']
	oldStock = 0
	inputCode = 0
	try:
		cursor.execute('''SELECT * FROM scrap_data WHERE keycode = %s''',[keycode])
		db.commit()
		urlData = cursor.fetchall()
		if(urlData == []):
			inputCode = 1
		else:
			for dat in urlData:
				if(dat[6]==""):
					oldStock = dat[7]
				if(dat[7]==""):
					oldStock = dat[6]
				#print(dat)
			inputCode = 0
	except Exception as e:
		print(str(e))
	print(oldStock)
	print(newStock)
#KALAU STOCK BEDA UPDATE STOCK_CHANGE_DATE
	if(int(oldStock)==int(newStock)):
		print("SAMA WOI")
	else:
		print("BEDA WOI")
	if(int(newStock) != int(oldStock) and inputCode==0):
		print("a")
		try:
			cursor.execute('''
			INSERT INTO scrap_data
				(identifier ,keycode,url, source, img_url, title, stock_1, stock_2, price_1, price_2, rating, stock_change_date, refreshed_date)
			VALUES
				(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
			ON DUPLICATE KEY UPDATE
				identifier = VALUES(identifier),
				url = VALUES(url),
				source = VALUES(source),
				img_url  = VALUES(img_url),
				title  = VALUES(title),
				stock_1  = VALUES(stock_1),
				stock_2  = VALUES(stock_2),
				price_1  = VALUES(price_1),
				price_2  = VALUES(price_2),
				rating  = VALUES(rating),
				stock_change_date  = VALUES(stock_change_date),
				refreshed_date  = VALUES(refreshed_date);
		 ''',
		(dbCode,keycode,temp['url'],temp['source'],temp['imgUrl'],temp['title'],temp['stock1'],temp['stock2'],temp['price1'],temp['price2'],temp['rating'],dateTimeNow,dateTimeNow)	 # python variables
					  )
			db.commit()
		except Exception as e:
			print(str(e))
	else:
		print("b")
		try:
			cursor.execute('''
			INSERT INTO scrap_data
				(identifier ,keycode,url, source, img_url, title, stock_1, stock_2, price_1, price_2, rating, stock_change_date, refreshed_date)
			VALUES
				(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
			ON DUPLICATE KEY UPDATE
				identifier = VALUES(identifier),
				url = VALUES(url),
				source = VALUES(source),
				img_url  = VALUES(img_url),
				title  = VALUES(title),
				stock_1  = VALUES(stock_1),
				stock_2  = VALUES(stock_2),
				price_1  = VALUES(price_1),
				price_2  = VALUES(price_2),
				rating  = VALUES(rating),
				#stock_change_date  = VALUES(stock_change_date),
				refreshed_date  = VALUES(refreshed_date);
		 ''',
		(dbCode,keycode,temp['url'],temp['source'],temp['imgUrl'],temp['title'],temp['stock1'],temp['stock2'],temp['price1'],temp['price2'],temp['rating'],dateTimeNow,dateTimeNow)	 # python variables
					  )
			db.commit()
		except Exception as e:
			print(str(e))

"""
def scrapeAdorama(adoramaURL):
	adoramaHeader={
	'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'accept-encoding':'gzip, deflate, br',
	'accept-language':'en-US,en;q=0.9',
	'cache-control':'no-cache',
	'cookie':'akCountry=ID; js_sid=1; sid3=820d6794-6e6f-4d45-8aec-01e17012da4f; lastPrtcl=https%3A; PUID=820d6794-6e6f-4d45-8aec-01e17012da4f; Adorama_ABTestingFlag=389; _pxvid=4a4776af-8da0-11ea-a851-0242ac120008; sr_browser_id=321ff0ed-bfbe-455f-bdef-3e678bc6129f; needlepin=1588553019384; SSID=CADmKx0OAAAAAAA0Za9ezVECDTRlr14CAAAAAAAAAAAA1NmxXgDo-GDJAAFnrhsA1NmxXgEA; SSSC=500.G6822783234720551373.2|51552.1814119; IsLoggedIn=False; adivparam=adnh-f_isVip-f_isLoggedIn-f; VipCustomer=F; isVip360=F; ShowMap=0|0|0|0; PHPSESSID=4hrm78jms9ftmu20ffg8t62bg1; HumanSrch=Sigma%20100-400%20C; SSOD=AB5dAAAAEACZMg4AAgAAACfbsV6h27FeAAA; SSRT=4t-xXgADAA; sailthru_pageviews=1; sailthru_content=ce31079a76f661fd351c8525b4ceb460; sailthru_visitor=64b6a436-72d9-4a19-bb40-38193515cf63; a=b; InvisibleParameter=priceMode%3D0%7C0%7C1%7C0%7C1%26pagePriceMode%3D0%7C0%7C0%7C0%7C0%26country%3DID%26productVersion%3D1420%26perPage%3D15%26sort%3D%26descSort%3D%26isVip%3Dfalse%26isSRLoggedIn%3Dfalse%26isVip360%3Dfalse%26isLoggedIn%3Dfalse%26mode%3D%26isFreeShipPromo%3Dfalse%26clientUtcOffset%3D7%26isEduPlus%3Dfalse%26bankId%3D1; activeUser=1; _px2=eyJ1IjoiYTg2MTZiZTAtOGYxYS0xMWVhLWIyYzEtOGYzYTdhYWYzZTQxIiwidiI6IjRhNDc3NmFmLThkYTAtMTFlYS1hODUxLTAyNDJhYzEyMDAwOCIsInQiOjE1ODg3MTU2NDU4MTIsImgiOiI2OGIzYmU4MjhiM2M5NTM1MjY4NDA5Zjk3NTMxYTU4NjQzMzJiYzk1ODkyMjc2ZTIwMjRiMTUzNmFmNzM3N2Q4In0=',
	'pragma':'no-cache',
	'sec-fetch-dest':'document',
	'sec-fetch-mode':'navigate',
	'sec-fetch-site':'none',
	'sec-fetch-user':'?1',
	'upgrade-insecure-requests':'1',
	'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36 OPR/67.0.3575.130',
	}
	#r = requests.get(adoramaURL)
	#return(r.text)

	driver = webdriver.Chrome(ChromeDriverManager().install())
	driver.get("https://www.adorama.com/msigs66037.html")

	form_element = driver.find_element_by_xpath("//h1/span").text
	print(form_element)
	return 0
"""
#shipping,review beloman
#print(sample_input['B&H'])
#test = scrapeAmazon("https://www.amazon.com/dp/B084B7GGNW")
#test = scrapeAmazon("https://www.amazon.com/dp/B07WTRXP7Y/ref=pd_vtpd_63_2/131-7347869-8361422?_encoding=UTF8&pd_rd_i=B07WTRXP7Y&pd_rd_r=ff2391ad-bbec-4713-a1eb-f94ff1fb400b&pd_rd_w=YO1JP&pd_rd_wg=WUPK4&pf_rd_p=be9253e2-366d-447b-83fa-e044efea8928&pf_rd_r=D755CGKGZ5RPQN8P76KE&psc=1&refRID=D755CGKGZ5RPQN8P76KE")
#print(test)
#test = scrapeAdorama("https://www.adorama.com/msigs66037.html") ## SKIPPED DUE TO ANTISCRIPT
#test = scrapeBB("https://www.bestbuy.com/site/msi-gs66-10sfs-15-6-laptop-intel-core-i7-32gb-memory-nvidia-geforce-rtx-2070-super-512gb-ssd-black-core/6408527.p?skuId=6408527")
#print(test)
#test = scrapeBH("https://www.bhphotovideo.com/c/product/1551636-REG/msi_gs66_stealth_10sfs_037_gs66_stealth_i7_10750h_rtx2070.html")
#print(test)


#print(db)

cursor.execute("""SELECT * FROM scrap_url""")
db.commit()
urlData = cursor.fetchall()

for dat in urlData:
	urlList = []
	dbCode = dat[0]
	temp = dat[1].strip()
	urlJson = simplejson.loads(temp)
	urlList.append([dbCode,"Bestbuy",urlJson['Bestbuy']])
	urlList.append([dbCode,"Amazon",urlJson['Amazon']])
	urlList.append([dbCode,"B&H",urlJson['B&H']])
	#print(urlList)

	try:
		with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
			futures = [executor.submit(runAll, url[0], url[1], url[2]) for url in urlList]

			kwargs = {
				'total': len(futures),
				'unit': 'Pages',
				'unit_scale': True,
				'leave': True
			}

			for x in tqdm(as_completed(futures), **kwargs):
				pass
	except Exception as e:
		print("Keywords error?")
		log.write(e+"\n")
		sleep(3)

	#break
#print(test)
#print(test['Bestbuy'])
cursor.close()
db.close()

driver.quit()
