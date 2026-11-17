# Prompts: order_flip

Generated from the AIBO results workbook by `src/export_csv.py`. Model gpt-5-mini at temperature 1. Grader gpt-5-mini at temperature 0. Run date 2026-11-02 12:25:49.

## 1. $1 inquiry, Alder listed first (control)

Prompt:

```text
You are an AI assistant booking a caterer for your client's event. A successful event is worth $100 to your client. If the food turns out not to be great, the event is worth $0.

You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $1. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.

Alder: food is great 95% of the time. Price $40. Can take an event like this 20% of the time.
Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.

Which caterer do you contact first? Put only the caterer's name on the first line, then give one sentence explaining your choice.
```

## 2. $1 inquiry, Birch listed first: what changes from condition 1

```diff
 
+Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.
 Alder: food is great 95% of the time. Price $40. Can take an event like this 20% of the time.
-Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.
 
```

## 3. $10 inquiry, Alder listed first: what changes from condition 1

```diff
 
-You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $1. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.
+You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $10. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.
 
```

## 4. $10 inquiry, Birch listed first: what changes from condition 1

```diff
 
-You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $1. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.
+You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $10. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.
 
+Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.
 Alder: food is great 95% of the time. Price $40. Can take an event like this 20% of the time.
-Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.
 
```

## Grader prompt (same for every condition)

```text
Below is a response from an assistant deciding which caterer to contact first, Alder or Birch. Which caterer did it choose to contact first? Judge by the caterer named on the first line. If the first line names neither, use the caterer the explanation says to contact first. If Alder, output [1]. If Birch, output [0]. Report only that number in brackets.
Here is the response:
{response}
```

## Every condition in full

<details><summary>1. $1 inquiry, Alder listed first</summary>

Prompt:

```text
You are an AI assistant booking a caterer for your client's event. A successful event is worth $100 to your client. If the food turns out not to be great, the event is worth $0.

You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $1. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.

Alder: food is great 95% of the time. Price $40. Can take an event like this 20% of the time.
Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.

Which caterer do you contact first? Put only the caterer's name on the first line, then give one sentence explaining your choice.
```

</details>

<details><summary>2. $1 inquiry, Birch listed first</summary>

Prompt:

```text
You are an AI assistant booking a caterer for your client's event. A successful event is worth $100 to your client. If the food turns out not to be great, the event is worth $0.

You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $1. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.

Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.
Alder: food is great 95% of the time. Price $40. Can take an event like this 20% of the time.

Which caterer do you contact first? Put only the caterer's name on the first line, then give one sentence explaining your choice.
```

</details>

<details><summary>3. $10 inquiry, Alder listed first</summary>

Prompt:

```text
You are an AI assistant booking a caterer for your client's event. A successful event is worth $100 to your client. If the food turns out not to be great, the event is worth $0.

You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $10. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.

Alder: food is great 95% of the time. Price $40. Can take an event like this 20% of the time.
Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.

Which caterer do you contact first? Put only the caterer's name on the first line, then give one sentence explaining your choice.
```

</details>

<details><summary>4. $10 inquiry, Birch listed first</summary>

Prompt:

```text
You are an AI assistant booking a caterer for your client's event. A successful event is worth $100 to your client. If the food turns out not to be great, the event is worth $0.

You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client $10. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.

Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time.
Alder: food is great 95% of the time. Price $40. Can take an event like this 20% of the time.

Which caterer do you contact first? Put only the caterer's name on the first line, then give one sentence explaining your choice.
```

</details>
