# How the OLH calculates supporter fees

*Last updated by Joe Muller on 16 June 2025.*

The OLH sets fees for supporting institutions based on where they are in the world, and how big they are. Institutions can also choose to contribute at a higher level.

There are five parts to calculating the fees:

1. setting base fees,
2. accounting for geographic location,
3. accounting for institution size,
4. converting the currency, and
5. adjusting for supporter level.

## 1. Base fee

We set our base fee in Euros, due to the instability of the British Pound over the last ten years. We also treat Germany as the geographic starting point, since Germany’s economy is quite stable and more embedded with a lot of our other supporters in Europe, which helps keep fees from fluctuating too much.

In 2024-25 our base fee was €1990:

> x = base fee
>
> x = 1990 EUR

## 2. Geographic location

We adjust for geographic location because of large global income disparities. We use data from the World Bank on gross national income (GNI) per capita to figure out the disparity between the supporter’s country and the geographic base we set (Germany in our case).

Here’s what it would look like for McGill University in Montreal:

> x = base fee * (Canada GNI / Germany GNI) 
>
> x = 1990 * (52,960 / 54,030)
>
> x = 1950 EUR

Note that all GNI per capita figures are in USD, but we do not need to convert them out of USD for the maths to work, since we are dividing one USD value by another.

## 3. Institution size

We charge higher fees to bigger universities, and lower fees to smaller research or teaching institutions. To get a number for size, we put institutions in size bands, and then assign a “multiplier” to each size.

| Size   | Description          | Multiplier |
|--------|----------------------|------------|
| Large  | 10,000+ students     | 1.33       |
| Medium | 5,000-9,999 students | 1.00       |
| Small  | 0-4,999 students     | 0.67       |

McGill has nearly 40,000 students:

> x = base fee * (Canada GNI / Germany GNI) * large size multiplier
>
> x = 1990 * (52,960 / 54,030) * 1.33
>
> x = 2590 EUR

## 4. Currency

Supporters can choose to be billed in Euros, British Pounds, or US Dollars.

We use the latest yearly average exchange rate when converting currencies, to avoid too much fluctuation. We get the rates from the World Bank.

If McGill were to choose US dollars, we would apply the exchange rate:

> x = base fee * (Canada GNI / Germany GNI) * large size multiplier * EUR to USD exchange rate
>
> x = 1990 * (52,960 / 54,030) * 1.33 * 1.05
>
> x = 2050 USD

That’s all we need to do for standard support levels.

## 5. Higher support

Institutions can choose to level up their support beyond the standard tier.

If they do that, we apply a different base fee (we have a different base fee for each tier).

We also do **not** apply any size multiplier for higher support levels.

If McGill were to become a “silver” supporter, we would use this calculation:

> x = silver base fee * (Canada GNI / Germany GNI) * EUR to USD exchange rate
>
> x = 9640 * (52,960 / 54,030) * 1.05
>
> x = 9920 USD

## More examples

### Glasgow School of Art as a Standard supporter

> x = base fee * (UK GNI / Germany GNI) * small size multiplier * EUR to GBP exchange rate
>
> x = 1990 * (49,240 / 54,030) * 0.67 * 0.84
>
> x = 1020 GBP

### University of the Witwatersrand as a Standard supporter

> x = base fee * (South Africa GNI / Germany GNI) * large size multiplier * EUR to USD exchange rate
>
> x = 1990 * (6,780 / 54,030) * 1.33 * 1.05
>
> x = 340 USD

### National Library of the Netherlands as a Silver supporter

> x = silver base fee * (Netherlands GNI / Germany GNI) * EUR to EUR exchange rate
>
> x = 9640 * (60,230 / 54,030) * 1.00
>
> x = 10,750 EUR

### Yale University as a Bronze supporter

> x = bronze base fee * (USA GNI / Germany GNI) * EUR to USD exchange rate
>
> x = 6420 * (76,770 / 54,030) * 1.05
>
> x = 9580 USD

## Yearly updates

This kind of calculation method requires regular updates to the underlying data. GNI per capita and exchange rates are always changing. On top of this, inflation will erode our yearly fees unless we raise them every year.

This is what we have to do each year:

  - put up base fees by inflation, usually around 3%, but more recently
  - download new GNI per capita tables from the World Bank
  - download new exchange rate data from the World Bank
