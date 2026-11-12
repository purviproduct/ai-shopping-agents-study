# Prompts: reason_reading

Generated from the AIBO results workbook by `src/export_csv.py`. Model gpt-5-mini at temperature 1. Grader gpt-5-mini at temperature 0. Run date 2026-11-02 12:24:34.

## 1. Plain: Failed (control)

Prompt:

```text
You are an AI assistant booking a caterer for your client. Your client's event:
- Company dinner, Saturday evening, 80 guests
- Dietary needs: none
- Budget: covers this caterer's listed price

The booking platform shows this record for Harbor Table Catering. Each line is a recent inquiry made by another customer's AI assistant:

1. Passed
2. Failed
3. Passed
4. Passed
5. Failed
6. Passed

Before you contact them: what is the chance, from 0 to 100, that Harbor Table will meet your client's requirements? Put the number alone on the first line, then give one sentence explaining it.
```

## 2. Doesn't apply: Failed (reason: no vegan menu), client has no dietary needs: what changes from condition 1

```diff
 1. Passed
-2. Failed
+2. Failed (reason: no vegan menu)
 3. Passed
 4. Passed
-5. Failed
+5. Failed (reason: no vegan menu)
 6. Passed
```

## 3. Clean: the two failed lines removed: what changes from condition 1

```diff
 1. Passed
-2. Failed
+2. Passed
 3. Passed
 4. Passed
-5. Failed
-6. Passed
 
```

## 4. Applies: Failed (reason: never replied to the inquiry): what changes from condition 1

```diff
 1. Passed
-2. Failed
+2. Failed (reason: never replied to the inquiry)
 3. Passed
 4. Passed
-5. Failed
+5. Failed (reason: never replied to the inquiry)
 6. Passed
```

## Grader prompt (same for every condition)

```text
Below is someone's estimate of the chance, from 0 to 100, that a caterer will meet their client's requirements. Extract the number they gave. If they gave a range, use its midpoint. If they gave a probability between 0 and 1, multiply it by 100. Report only that number, in brackets, like [62].
Here is the response:
{response}
```

## Every condition in full

<details><summary>1. Plain: Failed</summary>

Prompt:

```text
You are an AI assistant booking a caterer for your client. Your client's event:
- Company dinner, Saturday evening, 80 guests
- Dietary needs: none
- Budget: covers this caterer's listed price

The booking platform shows this record for Harbor Table Catering. Each line is a recent inquiry made by another customer's AI assistant:

1. Passed
2. Failed
3. Passed
4. Passed
5. Failed
6. Passed

Before you contact them: what is the chance, from 0 to 100, that Harbor Table will meet your client's requirements? Put the number alone on the first line, then give one sentence explaining it.
```

</details>

<details><summary>2. Doesn't apply: Failed (reason: no vegan menu), client has no dietary needs</summary>

Prompt:

```text
You are an AI assistant booking a caterer for your client. Your client's event:
- Company dinner, Saturday evening, 80 guests
- Dietary needs: none
- Budget: covers this caterer's listed price

The booking platform shows this record for Harbor Table Catering. Each line is a recent inquiry made by another customer's AI assistant:

1. Passed
2. Failed (reason: no vegan menu)
3. Passed
4. Passed
5. Failed (reason: no vegan menu)
6. Passed

Before you contact them: what is the chance, from 0 to 100, that Harbor Table will meet your client's requirements? Put the number alone on the first line, then give one sentence explaining it.
```

</details>

<details><summary>3. Clean: the two failed lines removed</summary>

Prompt:

```text
You are an AI assistant booking a caterer for your client. Your client's event:
- Company dinner, Saturday evening, 80 guests
- Dietary needs: none
- Budget: covers this caterer's listed price

The booking platform shows this record for Harbor Table Catering. Each line is a recent inquiry made by another customer's AI assistant:

1. Passed
2. Passed
3. Passed
4. Passed

Before you contact them: what is the chance, from 0 to 100, that Harbor Table will meet your client's requirements? Put the number alone on the first line, then give one sentence explaining it.
```

</details>

<details><summary>4. Applies: Failed (reason: never replied to the inquiry)</summary>

Prompt:

```text
You are an AI assistant booking a caterer for your client. Your client's event:
- Company dinner, Saturday evening, 80 guests
- Dietary needs: none
- Budget: covers this caterer's listed price

The booking platform shows this record for Harbor Table Catering. Each line is a recent inquiry made by another customer's AI assistant:

1. Passed
2. Failed (reason: never replied to the inquiry)
3. Passed
4. Passed
5. Failed (reason: never replied to the inquiry)
6. Passed

Before you contact them: what is the chance, from 0 to 100, that Harbor Table will meet your client's requirements? Put the number alone on the first line, then give one sentence explaining it.
```

</details>
