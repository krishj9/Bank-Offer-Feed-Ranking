import { expect, test } from 'vitest';
import { getCategoryDisplay, getEligibilityNotes, MOCK_USERS } from '../src/api/client';

test('getCategoryDisplay maps offer categories and types correctly', () => {
  expect(getCategoryDisplay('savings')).toBe('Savings');
  expect(getCategoryDisplay('credit')).toBe('Credit Cards');
  expect(getCategoryDisplay('advice')).toBe('Advisory');
});

test('getEligibilityNotes checks age and job rules for OFR-001', () => {
  const youngUser = {
    ...MOCK_USERS[0],
    age: 18,
    job: 'student'
  };
  const eligibleUser = {
    ...MOCK_USERS[0],
    age: 30,
    job: 'technician'
  };

  const youngNotes = getEligibilityNotes(youngUser, 'OFR-001');
  const eligibleNotes = getEligibilityNotes(eligibleUser, 'OFR-001');

  expect(youngNotes).toContain('Ineligible: Age 18 < 25');
  expect(youngNotes).toContain('Job is student (excluded)');
  expect(eligibleNotes).toBe('Age >= 25, job is not student or unemployed');
});

test('getEligibilityNotes checks housing rule for OFR-004', () => {
  const renter = {
    ...MOCK_USERS[0],
    housing: 'no'
  };
  const homeowner = {
    ...MOCK_USERS[0],
    housing: 'yes'
  };

  expect(getEligibilityNotes(renter, 'OFR-004')).toBe('Ineligible: User housing != yes');
  expect(getEligibilityNotes(homeowner, 'OFR-004')).toBe('User has housing loan (housing = yes)');
});
