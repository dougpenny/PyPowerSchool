#
# endpoints.py
#
# Copyright (c) 2022 Doug Penny
# Licensed under MIT
#
# See LICENSE.md for license information
#
# SPDX-License-Identifier: MIT
#

from typing import List, Dict


class CoreResourcesMixin:
    """
    The CoreResourcesMixin class contains public methods for the core
    PowerSchool resources.
    """

    #
    # Non-paging endpoints; these return a single records
    #
    async def course_for_dcid(self, course_dcid: int) -> Dict:
        """
        Retrieves the course with a given dcid.

        Args:
            course_dcid (int):
                DCID value for desired course

        Returns:
            A dictionary representing the retrieved course.
        """
        course_data = await self.fetch_item(f"ws/v1/course/{course_dcid}")
        return course_data.json()["course"]

    async def current_district(self, with_expansions: str = None) -> Dict:
        """
        Retrieves information about the current district.

        Returns:
            A dictionary representing the current district.
        """
        district_data = await self.fetch_item("ws/v1/district", expansions=with_expansions)
        return district_data.json()["district"]

    async def school_for_id(self, school_id: int, with_expansions: str = None) -> Dict:
        """
        Retrieves the school with a given ID.

        Args:
            school_id (int):
                ID value for desired school
            with_expansions (str, optional):
                Comma-delimited list of elements to expand

        Returns:
            A dictionary representing the retrieved school.
        """
        school_data = await self.fetch_item(f"ws/v1/school/{school_id}",
                                            expansions=with_expansions)
        return school_data.json()["school"]

    async def section_for_dcid(self, section_dcid: int, with_expansions: str = None) -> Dict:
        """
        Retrieves the section with a given dcid.

        Args:
            section_dcid (int):
                DCID value for desired section
            with_expansions (str, optional):
                Comma-delimited list of elements to expand

        Returns:
            A dictionary representing the retrieved section.
        """
        section_data = await self.fetch_item(f"ws/v1/section/{section_dcid}",
                                             expansions=with_expansions)
        return section_data.json()["section"]

    async def staff_for_dcid(self, staff_dcid: int, with_expansions: str = None) -> Dict:
        """
        Retrieves the staff with a given dcid.

        Args:
            staff_dcid (int):
                DCID value for desired staff
            with_expansions (str, optional):
                Comma-delimited list of elements to expand

        Returns:
            A dictionary representing the retrieved staff.
        """
        staff_data = await self.fetch_item(f"ws/v1/staff/{staff_dcid}",
                                           expansions=with_expansions)
        return staff_data.json()["staff"]

    async def student_for_dcid(self, student_dcid: int, with_expansions: str = None) -> Dict:
        """
        Retrieves the student with a given dcid.

        Args:
            student_dcid (int):
                DCID value for desired student
            with_expansions (str, optional):
                Comma-delimited list of elements to expand

        Returns:
            A dictionary representing the retrieved student.
        """
        student_data = await self.fetch_item(f"ws/v1/student/{student_dcid}",
                                             expansions=with_expansions)
        return student_data.json()["student"]

    async def term_for_dcid(self, term_dcid: int) -> str:
        """
        Retrieves the term with a given dcid.

        Args:
            term_dcid (int):
                DCID value for desired term

        Returns:
            A dictionary representing the retrieved term.
        """
        term_data = await self.fetch_item(f"ws/v1/term/{term_dcid}")
        return term_data.json()["term"]

    #
    # Paging endpoint; these return collections of items
    #
    async def courses_for_school(self, school_id: int) -> List:
        """
        Retrieves the courses for a given school.

        Args:
            school_id (int):
                ID value for the school

        Returns:
            A list of dictionaries representing the retrieved courses.
        """
        return await self.fetch_items(f"ws/v1/school/{school_id}/course")

    async def schools_in_district(self, with_expansions: str = None) -> List:
        """
        Retrieve all of the schools in the district.

        with_expansions (str, optional):
                Comma-delimited list of elements to expand

        Returns:
            A list of dictionaries representing the retrieved schools.
        """
        return await self.fetch_items("ws/v1/district/school", expansions=with_expansions)

    async def sections_for_school(self, school_id: int, with_expansions: str = None,
                                  query: str = None) -> List:
        """
        Retrieves the sections for a given school.

        Args:
            school_id (int):
                ID value for the school
            with_expansions (str, optional):
                Comma-delimited list of elements to expand
            query (str, optional):
                Criteria for selecting a subset of records

        Returns:
            A list of dictionaries representing the retrieved sections.
        """
        return await self.fetch_items(f"ws/v1/school/{school_id}/section",
                                      expansions=with_expansions, query=query)

    async def staff_for_school(self, school_id: int, with_expansions: str = None) -> List:
        """
        Retrieves all of the staff with a given school ID.

        Args:
            school_id (int):
                ID value for the school
            with_expansions (str, optional):
                Comma-delimited list of elements to expand

        Returns:
            A list of dictionaries representing the retrieved staff.
        """
        return await self.fetch_items(f"ws/v1/school/{school_id}/staff",
                                      expansions=with_expansions)

    async def students_for_school(self, school_id: int, with_expansions: str = None,
                                  query: str = None) -> List:
        """
        Retrieves all of the students with a given school ID.

        Args:
            school_id (int):
                ID value for the school
            with_expansions (str, optional):
                Comma-delimited list of elements to expand

        Returns:
            A list of dictionaries representing the retrieved students.
        """
        return await self.fetch_items(f"ws/v1/school/{school_id}/student",
                                      expansions=with_expansions, query=query)

    async def students_in_district(self, with_expansions: str = None, query: str = None) -> List:
        """
        Retrieves all of the students inthe current district.

        Args:
            with_expansions (str, optional):
                Comma-delimited list of elements to expand
            query (str, optional):
                Criteria for selecting a subset of records

        Returns:
            A list of dictionaries representing the retrieved students.
        """
        return await self.fetch_items("ws/v1/district/student",
                                      expansions=with_expansions, query=query)
